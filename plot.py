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
problem = 4
print(problems_name[problem])
for setting in range(6):
	plt.subplot(311)
	hyper_parameter_name=10*problem+setting
	li=[]
	for seed_num in range(10):
		try:
			temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/reutrn_"+str(seed_num)+".txt")
			li.append(temp)
		except:
			#print("problem")
			pass
	#print([len(x) for x in li])
	li=truncate(li)
	plt.plot(smooth(numpy.mean(li,axis=0)),label=hyper_parameter_name,lw=3)
	#plt.ylim([ylim_down[problem],ylim_up[problem]])
	#plt.yticks([ylim_down[problem],ylim_up[problem]])


	plt.subplot(312)
	hyper_parameter_name=10*problem+setting
	li=[]
	for seed_num in range(10):
		try:
			temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/safety_"+str(seed_num)+".txt")
			li.append(temp)
		except:
			#print("problem")
			pass
	#print([len(x) for x in li])
	li=truncate(li)
	plt.plot(smooth(numpy.mean(li,axis=0)),label=hyper_parameter_name,lw=3)
	#plt.ylim([ylim_down[problem],ylim_up[problem]])
	#plt.yticks([ylim_down[problem],ylim_up[problem]])

	plt.subplot(313)
	hyper_parameter_name=10*problem+setting
	li=[]
	for seed_num in range(10):
		try:
			temp=numpy.loadtxt("rbf_results/"+str(hyper_parameter_name)+"/lambda_"+str(seed_num)+".txt")
			li.append(temp)
		except:
			#print("problem")
			pass
	#print([len(x) for x in li])
	li=truncate(li)
	li_labels = ['0.0001','0.00025','0.0005','0.001','0.0025','0.005']
	plt.plot(smooth(numpy.mean(li,axis=0)),label=r'$\Delta \lambda$:'+li_labels[setting],lw=3)
	#plt.ylim([ylim_down[problem],ylim_up[problem]])
	#plt.yticks([ylim_down[problem],ylim_up[problem]])

plt.legend()

plt.show()