import gym, sys
import numpy, random
import utils_for_q_learning, buffer_class

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy

def rbf_function(centroid_locations, action, beta, N):
    centroid_locations_squeezed = [l.unsqueeze(1) for l in centroid_locations]
    centroid_locations_cat = torch.cat(centroid_locations_squeezed, dim=1)
    action_unsqueezed = action.unsqueeze(1)
    action_cat = torch.cat([action_unsqueezed for _ in range(N)], dim=1)
    diff = centroid_locations_cat - action_cat
    diff_norm = torch.norm(diff,p=2,dim=2)
    diff_norm_smoothed_negated = diff_norm * beta * -1
    output = F.softmax(diff_norm_smoothed_negated, dim=1)
    return output 

class Net(nn.Module):
	def __init__(self, params, env, state_size, action_size):
		super(Net, self).__init__()
		
		self.env = env
		self.params = params
		self.N = self.params['num_points']
		self.max_a = self.env.action_space.high[0]
		self.beta = self.params['temperature']

		self.buffer_object = buffer_class.buffer_class(max_length=self.params['max_buffer_size'])

		self.state_size, self.action_size = state_size, action_size

		self.value_side1 = nn.Linear(self.state_size, self.params['layer_size'])
		self.value_side1_parameters = self.value_side1.parameters()

		self.value_side2 = nn.Linear(self.params['layer_size'], self.params['layer_size'])
		self.value_side2_parameters = self.value_side2.parameters()

		self.value_side3 = nn.Linear(self.params['layer_size'], self.params['layer_size'])
		self.value_side3_parameters = self.value_side3.parameters()

		self.value_side4 = nn.Linear(self.params['layer_size'], self.N)
		self.value_side4_parameters = self.value_side4.parameters()

		self.location_side1 = nn.Linear(self.state_size, self.params['layer_size'])
		self.location_side2 = []
		for _ in range(self.N):
		    self.location_side2.append(nn.Linear(self.params['layer_size'], self.action_size))
		self.criterion = nn.MSELoss()


		params_dic=[]
		params_dic.append({'params': self.value_side1_parameters, 'lr': self.params['learning_rate']})
		params_dic.append({'params': self.value_side2_parameters, 'lr': self.params['learning_rate']})
		
		params_dic.append({'params': self.value_side3_parameters, 'lr': self.params['learning_rate']})
		params_dic.append({'params': self.value_side4_parameters, 'lr': self.params['learning_rate']})
		params_dic.append({'params': self.location_side1.parameters(), 'lr': self.params['learning_rate']}) 
		for i in range(self.N):
		    params_dic.append({'params': self.location_side2[i].parameters(), 'lr': self.params['learning_rate']}) 
		self.optimizer = optim.Adam(params_dic)

	def forward(self, s, a):
		centroid_values = self.get_centroid_values(s)
		centroid_locations = self.get_all_centroids(s)
		centroid_weights = rbf_function(centroid_locations, a, self.beta, self.N)
		output = torch.mul(centroid_weights,centroid_values)
		output = output.sum(1,keepdim=True)
		return output

	def get_centroid_values(self, s):
		temp = F.relu(self.value_side1(s))
		temp = F.relu(self.value_side2(temp))
		temp = F.relu(self.value_side3(temp))
		centroid_values = self.value_side4(temp)
		return centroid_values

	def get_all_centroids(self, s):
		temp = F.relu(self.location_side1(s))
		centroid_locations = []
		for i in range(self.N):
		    centroid_locations.append( self.max_a*torch.tanh(self.location_side2[i](temp)) )
		return centroid_locations

	def get_best_centroid(self, s, maxOrmin='max'):
		all_centroids = self.get_all_centroids(s)
		all_centroids_matrix = torch.cat(all_centroids, dim=0)
		weights = rbf_function(all_centroids, all_centroids_matrix, self.beta, self.N)
		values = self.get_centroid_values(s)
		values = torch.transpose(values, 0, 1)
		temp = torch.mm(weights,values)
		if maxOrmin=='max':
			values, indices = temp.max(0)
		elif maxOrmin=='min':
			values, indices = temp.min(0)
		Q_star = values.data.numpy()[0]
		index_star = indices.data.numpy()[0]
		a_star = list(all_centroids[index_star].data.numpy()[0])
		return Q_star, a_star

	def e_greedy_policy(self,s,episode,train_or_test):
		epsilon=1./numpy.power(episode,1./self.params['policy_parameter'])

		if train_or_test=='train' and random.random() < epsilon:
			a = self.env.action_space.sample()
			return a.tolist()
		else:
			s_matrix = numpy.array(s).reshape(1,self.state_size)
			q,a = self.get_best_centroid( torch.FloatTensor(s_matrix))
			return a

	def update(self, target_Q):

		if len(self.buffer_object.storage)<params['batch_size']:
			return
		else:
			pass
		batch=random.sample(self.buffer_object.storage,params['batch_size'])
		s_li=[b['s'] for b in batch]
		sp_li=[b['sp'] for b in batch]
		r_li=[b['r'] for b in batch]
		done_li=[b['done'] for b in batch]
		a_li=[b['a'] for b in batch]
		s_matrix=numpy.array(s_li).reshape(params['batch_size'],self.state_size)
		a_matrix=numpy.array(a_li).reshape(params['batch_size'],self.action_size)
		r_matrix=numpy.array(r_li).reshape(params['batch_size'],1)
		#print(r_matrix)
		#r_matrix=r_matrix-numpy.mean(self.all_rewards[-self.params['avg_reward']:])
		#print(r_matrix)
		#assert False
		r_matrix=numpy.clip(r_matrix,a_min=-self.params['reward_clip'],a_max=self.params['reward_clip'])
		sp_matrix=numpy.array(sp_li).reshape(params['batch_size'],self.state_size)
		done_matrix=numpy.array(done_li).reshape(params['batch_size'],1)
		Q_star_li=[]
		for sp in sp_matrix:
			Q_star, _=target_Q.get_best_centroid(torch.FloatTensor(sp.reshape(1,-1)))
			Q_star_li.append(Q_star)
		next_q_star_matrix = numpy.array(Q_star_li).reshape(params['batch_size'],1)
		y=r_matrix+self.params['gamma']*(1-done_matrix)*next_q_star_matrix

		self.optimizer.zero_grad()
		y_hat = self.forward(torch.FloatTensor(s_matrix),torch.FloatTensor(a_matrix))
		self.loss = self.criterion(y_hat,torch.FloatTensor(y))
		self.loss.backward()
		self.optimizer.step()
		self.optimizer.zero_grad()
		utils_for_q_learning.sync_networks(target = target_Q, online = self, alpha = params['target_network_learning_rate'], copy = False)

'''
class Q_class:

	def __init__(self,params,env,state_size,action_size):
		self.env=env
		self.params=params
		self.state_size,self.action_size=state_size,action_size
		self.network,self.qRef_li=self.create_network()
		self.target_network,self.target_qRef_li=self.create_network()
		self.target_network.set_weights(self.network.get_weights())
		self.buffer_object=buffer_class.buffer_class(max_length=self.params['max_buffer_size'])
		self.all_rewards=[]
		self.avg_reward=0

	def func_L2(self,tensors):
		return -K.sqrt(K.sum(K.square(tensors[0]-tensors[1]),
						axis=1,
						keepdims=True)+ self.params['norm_smoothing'])

	def create_network(self):
		state_input,action_input=Input(shape=(self.state_size,)), Input(shape=(self.action_size,))
		h = state_input
		for _ in range(self.params['num_layers']):	
			h = Dense(self.params['layer_size'])(h)
			h = Activation("relu")(h)				
		q_output = Dense(self.params['num_points'])(h)# value of anchor points
		try:
			print(self.params['deep_action_branch'])
			ha = Dense(512)(state_input)
			ha = Activation("relu")(ha)
			ha = keras.layers.Dropout(rate=0.4)(ha)
			ha = Dense(512)(ha)
			ha = Activation("relu")(ha)
			ha = keras.layers.Dropout(rate=0.4)(ha)
		except:
			ha = Dense(512)(state_input)
			ha = Activation("relu")(ha)
			ha = keras.layers.Dropout(rate=0.4)(ha)
		#define anchor point locations
		a_negative_distance_li,a_li,L2_layer=[],[],Lambda(self.func_L2,output_shape=(1,))
		for a_index in range(self.params['num_points']):
			temp = Dense(self.action_size,
							activation='tanh',#to ensure output is between -1 and 1
							kernel_initializer=RandomUniform(minval=-.1, maxval=+.1, seed=None),
							bias_initializer=RandomUniform(minval=-1, maxval=+1, seed=None))(ha)
			# now ensure output is between -high and high
			temp = Lambda(lambda x: x*self.env.action_space.high[0],(self.action_size,))(temp)
			a_li.append(temp)
			#get negative distance between a and each anchor point
			temp = L2_layer([temp,action_input])
			a_negative_distance_li.append(temp)
		a_negative_distance_cat=Concatenate(axis=-1)(a_negative_distance_li)
		#pass negative distance from softmax (with temperature)
		a_negative_distance_cat=Lambda(lambda x: x * self.params['temperature'],output_shape=(self.params['num_points'],))(a_negative_distance_cat)
		softmax=Activation('softmax')(a_negative_distance_cat)

		final_q=dot([q_output,softmax],axes=1, normalize=False)
		model = Model(inputs=[state_input, action_input], outputs=final_q)
		opt = optimizers.RMSprop(lr=self.params['learning_rate'],clipnorm=2.5)
		model.compile(loss='mse',optimizer=opt)


		qRef_li=[]
		for j in range(self.params['num_points']):
			each_qRef=[]
			for i in range(self.params['num_points']):
				each_qRef.append(L2_layer([a_li[i],a_li[j]]))
			each_qRef = Concatenate(axis=-1)(each_qRef)
			each_qRef = Lambda(lambda x: x * self.params['temperature'],output_shape=(self.params['num_points'],))(each_qRef)
			each_qRef = Activation('softmax')(each_qRef)
			test_final_q = dot([q_output,each_qRef],axes=1, normalize=False)
			qRef_li.append(test_final_q)
		# given a state, qRef_li gives anchor locations and their corresponding values ...
		qRef_li = Model(inputs=state_input,
					  outputs=[Concatenate(axis=1)(a_li),
							   Concatenate(axis=-1)(qRef_li)])

		return model,qRef_li

	def e_greedy_policy(self,s,episode,train_or_test):
		epsilon=1./numpy.power(episode,1./self.params['policy_parameter'])
		if train_or_test=='train' and random.random() < epsilon:
			a = self.env.action_space.sample()
			return a.tolist()

		else:
			s_matrix = numpy.array(s).reshape(1,self.state_size)
			aRef_li,qRef_li = self.qRef_li.predict(s_matrix)
			max_index = numpy.argmax(qRef_li)
			aRef_begin,aRef_end = max_index*self.action_size,(max_index+1)*self.action_size
			a = aRef_li[0,aRef_begin:aRef_end]
			return a.tolist()

	def update(self):
		if len(self.buffer_object.storage)<params['batch_size']:
			return
		else:
			pass
		batch=random.sample(self.buffer_object.storage,params['batch_size'])
		s_li=[b['s'] for b in batch]
		sp_li=[b['sp'] for b in batch]
		r_li=[b['r'] for b in batch]
		done_li=[b['done'] for b in batch]
		a_li=[b['a'] for b in batch]
		s_matrix=numpy.array(s_li).reshape(params['batch_size'],self.state_size)
		a_matrix=numpy.array(a_li).reshape(params['batch_size'],self.action_size)
		r_matrix=numpy.array(r_li).reshape(params['batch_size'],1)
		#print(r_matrix)
		#r_matrix=r_matrix-numpy.mean(self.all_rewards[-self.params['avg_reward']:])
		#print(r_matrix)
		#assert False
		r_matrix=numpy.clip(r_matrix,a_min=-self.params['reward_clip'],a_max=self.params['reward_clip'])
		sp_matrix=numpy.array(sp_li).reshape(params['batch_size'],self.state_size)
		done_matrix=numpy.array(done_li).reshape(params['batch_size'],1)

		next_aRef_li,next_qRef_li=self.target_qRef_li.predict(sp_matrix)
		next_qRef_star_matrix=numpy.max(next_qRef_li,axis=1,keepdims=True)
		label=r_matrix+self.params['gamma']*(1-done_matrix)*next_qRef_star_matrix
		self.network.fit(x=[s_matrix,a_matrix],
						y=label,
						epochs=self.params['updates_per_batch'],
						batch_size=params['batch_size'],
						verbose=0)
		self.update_target_net()

	def update_target_net(self):
		network_weights=self.network.get_weights()
		target_weights=self.target_network.get_weights()
		new_target_weights=[]
		for n,t in zip(network_weights,target_weights):
			temp=self.params['target_network_learning_rate']*n+(1-self.params['target_network_learning_rate'])*t
			new_target_weights.append(temp)
		self.target_network.set_weights(new_target_weights)
'''
if __name__=='__main__':
	hyper_parameter_name=sys.argv[1]
	alg='rbf'
	params=utils_for_q_learning.get_hyper_parameters(hyper_parameter_name,alg)
	params['hyper_parameters_name']=hyper_parameter_name
	env=gym.make(params['env_name'])
	#env = gym.wrappers.Monitor(env, 'videos/'+params['env_name']+"/", video_callable=lambda episode_id: episode_id%10==0,force = True)
	params['env']=env
	params['seed_number']=int(sys.argv[2])
	utils_for_q_learning.set_random_seed(params)
	s0=env.reset()
	utils_for_q_learning.action_checker(env)
	Q_object = Net(params,env,state_size=len(s0),action_size=len(env.action_space.low))
	Q_object_target = Net(params,env,state_size=len(s0),action_size=len(env.action_space.low))
	print("now sync networks ... ")
	utils_for_q_learning.sync_networks(target = Q_object_target, online = Q_object, alpha = params['target_network_learning_rate'],copy = True)

	G_li=[]
	for episode in range(params['max_episode']):
		#train policy with exploration
		s,done=env.reset(),False
		while done==False:
			a=Q_object.e_greedy_policy(s,episode+1,'train')
			sp,r,done,_=env.step(numpy.array(a))
			Q_object.buffer_object.append(s,a,r,done,sp)
			s=sp

		#now update the Q network
		for _ in range(params['updates_per_episode']):
			Q_object.update(Q_object_target)

		#test the learned policy, without performing any exploration
		s,t,G,done=env.reset(),0,0,False
		while done==False:
			a=Q_object.e_greedy_policy(s,episode+1,'test')
			sp,r,done,_=env.step(numpy.array(a))
			s,t,G=sp,t+1,G+r
		print("in episode {} we collected return {} in {} timesteps".format(episode,G,t))
		G_li.append(G)
		if episode % 10 == 0 and episode>0:	
			utils_for_q_learning.save(G_li,params,alg)
			#Q_object.network.save_weights("rbf_policies/"+hyper_parameter_name+"_model.h5")

	utils_for_q_learning.save(G_li,params,alg)