import gym, sys
import numpy, random
import utils_for_q_learning, buffer_class

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import numpy

def rbf_function_single(centroid_locations, beta, N, norm_smoothing):
	'''
		no batch
		given N centroids * size of each centroid
		determine weight of each centroid at each other centroid
	'''
	diff_norm_smoothed_negated = []
	centroid_locations_cat = torch.cat(centroid_locations, dim=0)
	for i in range(N):
		centroid_i = centroid_locations_cat[i,:].unsqueeze(0)
		centroid_i = torch.cat([centroid_i for _ in range(N)],dim=0)
		diff_i = centroid_locations_cat - centroid_i
		#diff_norm_i = torch.norm(diff_i,p=2,dim=1)
		#print(diff_norm_i)
		diff_norm_i = diff_i**2
		diff_norm_i = torch.sum(diff_norm_i, dim=1)
		diff_norm_i = diff_norm_i + norm_smoothing
		diff_norm_i = torch.sqrt(diff_norm_i)

		diff_norm_smoothed_negated_i = diff_norm_i * beta * -1
		diff_norm_smoothed_negated_i = diff_norm_smoothed_negated_i.unsqueeze(0)
		diff_norm_smoothed_negated.append(diff_norm_smoothed_negated_i)

	diff_norm_smoothed_negated = torch.cat(diff_norm_smoothed_negated,dim=0)
	weights = F.softmax(diff_norm_smoothed_negated, dim=1)
	return weights

def rbf_function(centroid_locations, action, beta, N, norm_smoothing):
	'''
		given batch size * N centroids * size of each centroid
		and batch size * size of each action, determine the weight of
		each centroid for the action 
	'''
	centroid_locations_squeezed = [l.unsqueeze(1) for l in centroid_locations]
	centroid_locations_cat = torch.cat(centroid_locations_squeezed, dim=1)
	action_unsqueezed = action.unsqueeze(1)
	action_cat = torch.cat([action_unsqueezed for _ in range(N)], dim=1)
	diff = centroid_locations_cat - action_cat
	#diff_norm = torch.norm(diff,p=2,dim=2)
	diff_norm = diff**2
	diff_norm = torch.sum(diff_norm, dim=2)
	diff_norm = diff_norm + norm_smoothing
	diff_norm = torch.sqrt(diff_norm)

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

		self.drop = nn.Dropout(p=self.params['dropout_rate'])

		self.location_side1 = nn.Linear(self.state_size, self.params['layer_size'])
		torch.nn.init.xavier_uniform_(self.location_side1.weight)
		torch.nn.init.zeros_(self.location_side1.bias)

		if self.params['num_layers_action_side'] == 2:
			###
			self.location_side1point5 = nn.Linear(self.params['layer_size'], self.params['layer_size'])
			torch.nn.init.xavier_uniform_(self.location_side1point5.weight)
			torch.nn.init.zeros_(self.location_side1point5.bias)
			###

		self.location_side2 = []
		for _ in range(self.N):
			temp = nn.Linear(self.params['layer_size'], self.action_size)
			temp.weight.data.uniform_(-.1, .1)
			temp.bias.data.uniform_(-1, +1)
			#nn.init.uniform_(temp.bias,a = -2.0, b = +2.0)
			self.location_side2.append(temp)
		self.location_side2 = torch.nn.ModuleList(self.location_side2)
		self.criterion = nn.MSELoss()


		self.params_dic=[]
		self.params_dic.append({'params': self.value_side1_parameters, 'lr': self.params['learning_rate']})
		self.params_dic.append({'params': self.value_side2_parameters, 'lr': self.params['learning_rate']})
		
		self.params_dic.append({'params': self.value_side3_parameters, 'lr': self.params['learning_rate']})
		self.params_dic.append({'params': self.value_side4_parameters, 'lr': self.params['learning_rate']})
		self.params_dic.append({'params': self.location_side1.parameters(), 'lr': self.params['learning_rate_location_side']})

		if self.params['num_layers_action_side'] == 2:
			###
			self.params_dic.append({'params': self.location_side1point5.parameters(), 'lr': self.params['learning_rate_location_side']}) 
			###

		for i in range(self.N):
		    self.params_dic.append({'params': self.location_side2[i].parameters(), 'lr': self.params['learning_rate_location_side']}) 
		if self.params['optimizer']=='RMSprop':
			self.optimizer = optim.RMSprop(self.params_dic)
		elif self.params['optimizer']=='Adam':
			self.optimizer = optim.Adam(self.params_dic)

	def forward(self, s, a):
		centroid_values = self.get_centroid_values(s)
		centroid_locations = self.get_all_centroids(s)
		centroid_weights = rbf_function(centroid_locations, a, self.beta, self.N, self.params['norm_smoothing'])
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
		temp = self.drop(temp)

		if self.params['num_layers_action_side'] == 2:
			###
			temp = F.relu(self.location_side1point5(temp))
			temp = self.drop(temp)
			###

		centroid_locations = []
		for i in range(self.N):
		    centroid_locations.append( self.max_a*torch.tanh(self.location_side2[i](temp)) )
		return centroid_locations

	def get_best_centroid(self, s, maxOrmin='max'):
		all_centroids = self.get_all_centroids(s)
		weights = rbf_function_single(all_centroids, self.beta, self.N, self.params['norm_smoothing'])
		#print(weights)
		#assert False
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
	
	def get_best_centroid_batch(self, s):
		'''
			given a batch of states s
			determine max_{a} Q(s,a)
		'''
		all_centroids = self.get_all_centroids(s)
		values = self.get_centroid_values(s)
		li=[]
		for i in range(self.N):
			#print(all_centroids[i].shape)
			weights = rbf_function(all_centroids, all_centroids[i], self.beta, self.N, self.params['norm_smoothing'])
			temp = torch.sum(torch.mul(weights,values), dim=1, keepdim=True)
			li.append(temp)
		allQ=torch.cat(li,dim=1)
		best,_ = allQ.max(1)
		return best.data.numpy()


	def e_greedy_policy(self,s,episode,train_or_test):
		epsilon=1./numpy.power(episode,1./self.params['policy_parameter'])

		if train_or_test=='train' and random.random() < epsilon:
			a = self.env.action_space.sample()
			return a.tolist()
		else:
			self.eval()
			s_matrix = numpy.array(s).reshape(1,self.state_size)
			q,a = self.get_best_centroid( torch.FloatTensor(s_matrix))
			self.train()
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

		r_matrix=numpy.clip(r_matrix,a_min=-self.params['reward_clip'],a_max=self.params['reward_clip'])
		sp_matrix=numpy.array(sp_li).reshape(params['batch_size'],self.state_size)
		done_matrix=numpy.array(done_li).reshape(params['batch_size'],1)
		#self.train()
		Q_star = target_Q.get_best_centroid_batch(torch.FloatTensor(sp_matrix))
		#print(Q_star[0])
		#Q_star = target_Q.get_best_centroid_batch(torch.FloatTensor(sp_matrix))
		#print(Q_star[0])
		#assert False
		#assert False
		Q_star = Q_star.reshape((params['batch_size'],-1))
		#print(Q_star.shape)
		y=r_matrix+self.params['gamma']*(1-done_matrix)*Q_star
		
		y_hat = self.forward(torch.FloatTensor(s_matrix),torch.FloatTensor(a_matrix))
		loss = self.criterion(y_hat,torch.FloatTensor(y))
		self.zero_grad()
		loss.backward()
		self.optimizer.step()
		self.zero_grad()
		utils_for_q_learning.sync_networks(target = target_Q,
										   online = self, 
										   alpha = params['target_network_learning_rate'], 
										   copy = False)


def str_mj_arr(arr):
    return ' '.join(['%0.3f' % arr[i] for i in range(arr._length_)])

def print_contact_info(env):
    d = env.unwrapped.data
    for coni in range(d.ncon):
        #print('  Contact %d:' % (coni,))
        con = d.obj.contact[coni]
        #print('    dist     = %0.3f' % (con.dist,))
        #print('    pos      = %s' % (str_mj_arr(con.pos),))
        #print('    frame    = %s' % (str_mj_arr(con.frame),))
        #print('    friction = %s' % (str_mj_arr(con.friction),))
        ##print('    dim      = %d' % (con.dim,))
        #print('    geom1    = %d' % (con.geom1,))
        #print('    geom2    = %d' % (con.geom2,))
        #geom2 is 2 is good for us
        #1 is good too
        if int(con.geom2) == 1 or int(con.geom2) == 2:
            print("UNSAFE")
       
def is_safe(params):
	env = params["env"]
	if params["env_name"] == 'HalfCheetah-v1':
	    d = env.unwrapped.data
	    ret = 1
	    for coni in range(d.ncon):
	        con = d.obj.contact[coni]
	        if int(con.geom2) == 1 or int(con.geom2) == 2:
	            ret = 0
	    return(ret)
	elif params["env_name"] == 'Pendulum-v0':
		if abs(s[-1])>4:
			#print(s[-1])
			return 0
		return 1
	else:
		print("safety not defined for this domain yet")
		assert False

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
	Q_object_target.eval()

	utils_for_q_learning.sync_networks(target = Q_object_target, online = Q_object, alpha = params['target_network_learning_rate'], copy = True)

	G_li=[]
	safety_li=[]
	for episode in range(params['max_episode']):
		#train policy with exploration
		s,done=env.reset(),False
		#print(s)
		#print(type(s))
		#assert False
		while done==False:
			a=Q_object.e_greedy_policy(s,episode+1,'train')
			#print(s,a)
			sp,r,done,_=env.step(numpy.array(a))
			Q_object.buffer_object.append(s,a,r,done,sp)
			s=sp

		#now update the Q network
		for _ in range(params['updates_per_episode']):
			Q_object.update(Q_object_target)

		#test the learned policy, without performing any exploration
		s,t,G,done,safe=env.reset(),0,0,False,0
		while done==False:
			#print(env.env.model)
			#print(env.env.data.qpos)
			a=Q_object.e_greedy_policy(s,episode+1,'test')
			#print(episode, t , s , a)
			sp,r,done,_=env.step(numpy.array(a))
			s,t,G=sp,t+1,G+r
			#print("============================================")
			safe = is_safe(params)+safe
			#input()
			#env.render()
		#print(env.env.data.qpos[0])
		print("safety density", safe/t)
		print("in episode {} we collected return {} in {} timesteps".format(episode,G,t))
		G_li.append(G)
		safety_li.append(safe/t)
		if episode % 5 == 0 and episode>0:	
			utils_for_q_learning.save(G_li,params,alg,for_safety=False)
			utils_for_q_learning.save(safety_li,params,alg,for_safety=True)
			#Q_object.network.save_weights("rbf_policies/"+hyper_parameter_name+"_model.h5")

	utils_for_q_learning.save(G_li,params,alg,for_safety=False)
	utils_for_q_learning.save(safety_li,params,alg,for_safety=True)
