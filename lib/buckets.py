import subprocess
import boto3

from seekraux import * 
#######################################################################
					#Identify S3 Buckets#
#######################################################################
def output_buckets(profile):
	print """\033[1;31m            *#(/,            
          #%%%((((/          
   ..     #%%%((((/    ...   
  #%((((((%%%%(((((#%%%%#(*  
  #%(((((((#%%&&%%%%%%%%#(*  
  #%(((((((((####%%%%%%%#(*  
  #%((((((%%%%(((((%%%%%#(*  
  #%((((((%%%%(((((%%%%%#(*  
  #%((((((%%%%(((((%%%%%#(*  
  #%((((((((((#%%%%%%%%%#(*  
  #%((((((/**,,,*/(%%%%%#(*  
  #%(((((*%%%%(((((/#%%%#(*  
          #%%%((((/          
          #%%%((((/          
            .((*                                   
\033[0m"""
	print "Checking S3 Buckets for {}\n".format(profile)
	s3_output = subprocess.Popen([
    	'aws',
    	's3api',
    	'list-buckets',
    	'--profile',
    	'{}'.format(profile),
    	], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

	json_blob = s3_output.communicate()[0]

	cut_s3 = subprocess.Popen([
		'jq',
		'.Buckets[].Name',
		], stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr=subprocess.STDOUT)

	#out = cut_s3.communicate(json_blob)[0].split('\n')

	##NEW BOTO3 CALL METHOD:
	session = boto3.Session(profile_name='{}'.format(profile))
	out = session.resource('s3').buckets.all()
	#MUCH SIMPLER

	anywarnings = False
	bacl = False
	bpolicy = False
	for entry in out:

		bucket_acl =subprocess.Popen([
    		'aws',
    		's3api',
    		'get-bucket-acl',
    		'--bucket',
    		#'{}'.format(entry.replace('"', '')),
    		'{}'.format(entry.name),
    		'--profile',
    		'{}'.format(profile),
    		], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		acl = bucket_acl.communicate()
		#acl2 = session.resource('s3').BucketAcl('{}'.format(entry)).load()
		#print (acl2)
		for i in range(0,2):
			acls = subprocess.Popen([
				'jq',
				'.Grants[{}]'.format(i),
				], stdin=subprocess.PIPE, stdout = subprocess.PIPE, stderr=subprocess.STDOUT)
			value = acls.communicate(acl[0])

			if "AllUsers" in "{}".format(value):
				anywarnings = True
				bacl = True

				if "READ" in "{}".format(value):
					print "[" + bcolors.WARNING + bcolors.BOLD + "!" + bcolors.ENDC + "] ........ {} contains an ACL with READ access for ALL USERS.".format(entry.name)
				else:
					print "[" + bcolors.FAIL + bcolors.BOLD + u"\u2716" + bcolors.ENDC + "] ........ {} contains an ACL with WRITE access for ALL USERS.".format(entry.name)
			if "AuthenticatedUsers" in "{}".format(value):
				anywarnings = True

				if "READ" in "{}".format(value):
					print "[" + bcolors.WARNING + bcolors.BOLD + "!" + bcolors.ENDC + "] ........ {} contains an ACL with READ access for users within the console.".format(entry.name)
				else:
					print "[" + bcolors.WARNING + bcolors.BOLD + "!" + bcolors.ENDC + "] ........ {} contains an ACL with WRITE access for users within the console.".format(entry.name)

		bucket_policy =subprocess.Popen([
    		'aws',
    		's3api',
    		'get-bucket-policy',
    		'--bucket',
    		#'{}'.format(entry.replace('"', '')),
    		'{}'.format(entry.name),
    		'--profile',
    		'{}'.format(profile),
    		], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
		policy = bucket_policy.communicate()

		if "\"Effect\\\\\":\\\\\"Allow\\\\\",\\\\\"Principal\\\\\":\\\\\"*\\\\\"" in "{}".format(policy):
			bpolicy = True
			if "GetObject" in "{}".format(policy):
				print "[" + bcolors.WARNING + bcolors.BOLD + "!" + bcolors.ENDC + "] ........ {} contains Bucket Policy with READ access for ALL USERS.".format(entry.name)
			if "PutObject" in "{}".format(policy):
				print "[" + bcolors.FAIL + bcolors.BOLD + "!" + bcolors.ENDC + "] ........ {} contains an Bucket Policy with WRITE access for ALL USERS.".format(entry.name)

	if bacl == False:
		print "[" + bcolors.OKGREEN + u"\u2713" + bcolors.ENDC + "] No S3 Buckets with public ACLs have been identified."
	if bpolicy == False:
		print "[" + bcolors.OKGREEN + u"\u2713" + bcolors.ENDC + "] No S3 Buckets with public Bucket Policies have been identified."
	print ""
	return

	#if out != '':
		#print "[" + bcolors.FAIL + u"\u2716" + bcolors.ENDC + "] Public security groups identified. Please remediate immediately:"
		#print "{}\n".format(out)
		#if args.email:
			#send_warning(profile, "Public security groups identified. Please remediate immediately.", out)
	#else:
		#print "[" + bcolors.OKGREEN + u"\u2713" + bcolors.ENDC + "] No security groups with public rules have been identified.\n"
	#return