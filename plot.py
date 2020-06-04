import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import numpy

def truncate(li):
	#print([len(x) for x in li])
	N=numpy.min([len(x) for x in li])
	return [l[:N] for l in li]
def smooth(li):
	window=10
	y=li
	y_smooth=[numpy.mean(y[max(x-window,0):x+window]) for x in range(len(y))]
	return y_smooth

#[20,31,40,45]
#for hyper_parameter_name in ['10','11','12','13','14','15','16','17','lunar_old']:
#for hyper_parameter_name in [0,1,2,3]:
#for hyper_parameter_name in [20,21,22,23]:
#for hyper_parameter_name in range(40,55):
#for hyper_parameter_name in range(70,82):
#for hyper_parameter_name in range(82,85):
#for hyper_parameter_name in range(85,100):
problems_name=['Pendulum_reward','LunarLander','Bipedal','Ant','Cheetah_reward',
			   'Hopper','InvertedDoublePendulum','InvertedPendulum',
			   'Reacher']
ylim_down = [-1500,-350,-100,-500,-500,-500,0,0,-80]
ylim_up = [-100,235,300,3000,8000,3000,9350,1000,-4]
#y_ticks = [[-1000,-150],[-200,220],[0,250],[0,2500],[0,7500],[0,3000],[0,9000],[0,1000],[-50,-4]]
#setting_li=[0]
#setting_li=[0]+list(range(900,910))
#setting_li=[0]
for ind, problem in enumerate([0,4]):
	plt.subplot(3,4,2*ind+1)
	print(problems_name[problem])
	for setting in [0,1,2,3,4,5,6]:
		hyper_parameter_name=10*problem+setting
		li=[]
		for seed_num in range(20):
			try:
				temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/reutrn_"+str(seed_num)+".txt")
				li.append(temp)
			except:
				#print("problem")
				pass
		#print([len(x) for x in li])
		li=truncate(li)
		plt.plot(smooth(numpy.mean(li,axis=0)),label=hyper_parameter_name,lw=3)
		plt.ylim([ylim_down[problem],ylim_up[problem]])
		plt.yticks([ylim_down[problem],ylim_up[problem]])
	plt.title(problems_name[problem])
	plt.legend()

##########
problems_name=['Pendulum_reward','LunarLander','Bipedal','Ant','Cheetah_reward',
			   'Hopper','InvertedDoublePendulum','InvertedPendulum',
			   'Reacher']
ylim_down = [-1500,-350,-100,-500,-500,-500,0,0,-80]
ylim_up = [-100,235,300,3000,8000,3000,9350,1000,-4]
#y_ticks = [[-1000,-150],[-200,220],[0,250],[0,2500],[0,7500],[0,3000],[0,9000],[0,1000],[-50,-4]]
#setting_li=[0]
#setting_li=[0]+list(range(900,910))
#setting_li=[0]
for ind, problem in enumerate([0,4]):
	means=[]
	plt.subplot(3,4,2*ind+2)
	print(problems_name[problem])
	for setting in [0,1,2,3,4,5,6]:
		hyper_parameter_name=10*problem+setting
		li=[]
		for seed_num in range(20):
			try:
				temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/reutrn_"+str(seed_num)+".txt")
				li.append(temp)
			except:
				#print("problem")
				pass
		#print([len(x) for x in li])
		li=truncate(li)
		means.append(numpy.mean(li))
	print(means)
	plt.plot(means,lw=3)
	#plt.ylim([ylim_down[problem],ylim_up[problem]])
	#plt.yticks([ylim_down[problem],ylim_up[problem]])
	plt.title(problems_name[problem])
	#plt.legend()
##########

problems_name=['Pendulum_safety','LunarLander','Bipedal','Ant','Cheetah_safety',
			   'Hopper','InvertedDoublePendulum','InvertedPendulum',
			   'Reacher']
for ind, problem in enumerate([0,4]):
	plt.subplot(3,4,4+ ind*2 +1)
	print(problems_name[problem])
	for setting in [0,1,2,3,4,5,6]:
		hyper_parameter_name=10*problem+setting
		li=[]
		for seed_num in range(20):
			try:
				temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/safety_"+str(seed_num)+".txt")
				li.append(temp)
				#print(len(temp))
			except:
				#print("problem")
				pass
		#print([len(x) for x in li])
		li=truncate(li)
		plt.plot(smooth(numpy.mean(li,axis=0)),label=hyper_parameter_name,lw=3)
		plt.ylim([0.7,1])
		#plt.yticks([0.7,1])
	plt.title(problems_name[problem])
	plt.legend()
########
problems_name=['Pendulum_safety','LunarLander','Bipedal','Ant','Cheetah_safety',
			   'Hopper','InvertedDoublePendulum','InvertedPendulum',
			   'Reacher']
for ind, problem in enumerate([0,4]):
	means=[]
	plt.subplot(3,4,4+ ind*2 +2)
	print(problems_name[problem])
	for setting in [0,1,2,3,4,5,6]:
		hyper_parameter_name=10*problem+setting
		li=[]
		for seed_num in range(20):
			try:
				temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/safety_"+str(seed_num)+".txt")
				li.append(temp)
			except:
				#print("problem")
				pass
		#print([len(x) for x in li])
		li=truncate(li)
		means.append(numpy.mean(li))
	plt.plot(means,lw=3)
	plt.title(problems_name[problem])
	#plt.legend()
problems_name=['Pendulum_safety_and_return','LunarLander','Bipedal','Ant','Cheetah_safety_and_return',
			   'Hopper','InvertedDoublePendulum','InvertedPendulum',
			   'Reacher']
##########

for ind, problem in enumerate([0,4]):
	plt.subplot(3,4,8+ ind*2+1)
	print(problems_name[problem])
	for setting in [0,1,2,3,4,5,6]:
		hyper_parameter_name=10*problem+setting
		li=[]
		for seed_num in range(20):
			try:
				temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/return_and_safety_"+str(seed_num)+".txt")
				li.append(temp)
			except:
				#print("problem")
				pass
		#print([len(x) for x in li])
		li=truncate(li)
		plt.plot(smooth(numpy.mean(li,axis=0)),label=hyper_parameter_name,lw=3)
		plt.ylim([ylim_down[problem],ylim_up[problem]])
		plt.yticks([ylim_down[problem],ylim_up[problem]])
	plt.title(problems_name[problem])
	plt.legend()
#########
for ind, problem in enumerate([0,4]):
	means=[]
	plt.subplot(3,4,8+ ind*2+2)
	print(problems_name[problem])
	for setting in [0,1,2,3,4,5,6]:
		hyper_parameter_name=10*problem+setting
		li=[]
		for seed_num in range(20):
			try:
				temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/return_and_safety_"+str(seed_num)+".txt")
				#print(len(temp))
				li.append(temp)
			except:
				#print("problem")
				pass
		#print([len(x) for x in li])
		li=truncate(li)
		means.append(numpy.mean(li))
	print(means)
	plt.plot(means,lw=3)
	#plt.ylim([ylim_down[problem],ylim_up[problem]])
	#plt.yticks([ylim_down[problem],ylim_up[problem]])
	plt.title(problems_name[problem])
	#plt.legend()

plt.subplots_adjust(wspace=0.5,hspace = 1)

plt.show()