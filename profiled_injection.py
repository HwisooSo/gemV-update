import os
import sys
import random
import re

arch = sys.argv[1]
bench = sys.argv[2]
injectArch = sys.argv[3]
start = sys.argv[4]
end = sys.argv[5]
profiledFile = sys.argv[6]
selectiveInput = open(profiledFile, 'r')

gem5_binary = ''
#if(len(sys.argv) >= 7):
#   gem5_binary = sys.argv[6]

#HwiSoo: stringsearch sha bitcount qsort susan jpeg done
if(bench == 'hello'):
    runtime = 1203432
elif(bench == 'matmul'):
    runtime = 102119000 #valid for DC LAB server
elif(bench == 'stringsearch'):
    runtime = 96401000 #valid for DC LAB server
elif(bench == 'susan'):
    runtime = 1184289000 #valid for DC LAB server
elif(bench == 'gsm'):
    runtime = 15973624000 #valid for DC LAB server
elif(bench == 'jpeg'):
    runtime = 10380764000 #valid for DC LAB server
elif(bench == 'bitcount'):
    runtime = 1284616500 #valid for DC LAB server
elif(bench == 'qsort'):
    runtime = 12622084000 #valid for DC LAB server
elif(bench == 'dijkstra'):
    runtime = 27277285000 #valid for DC LAB server
elif(bench == 'basicmath'):
    runtime = 251651656000 #valid for DC LAB server
elif(bench == 'crc'):
    runtime = 1091403357500 #valid for DC LAB server
elif(bench == 'fft'):
    runtime = 28748840000
elif(bench == 'typeset'):
    runtime = 83872940000
elif(bench == 'patricia'):
    runtime = 99999999999999
elif(bench == 'sha'):
    runtime = 2782611000
elif(bench == 'ispell'):
    runtime = 99999999999999

os.system("mkdir " + str(bench))
#f = open(str(bench) + "/val_" + str(injectArch)+"_"+str(start)+"_"+str(end)+".txt", 'w') 

os.system("rm -rf " + str(bench) + "/val_" + str(injectArch)+"_"+str(start)+"_"+str(end)+".txt")
os.system("rm -rf " + str(bench) + "/sec_" + str(injectArch)+"_"+str(start)+"_"+str(end)+".txt")

for i in range(int(start), int(end)):
    if (injectArch == "NO"):
        injectLoc = 0
    elif (injectArch == "Reg"):
        line = selectiveInput.readline()
        injectTime = int(line.split()[1])
        injectIndex = int(line.split()[0])
        injectLoc = injectIndex*32+random.randrange(0,32)
    elif (injectArch == "FU"):
        injectLoc = random.randrange(1,15)
    elif (injectArch == "LSQ"):
                injectIndex = random.randrange(0,8)
                injectLoc = random.randrange(0,96)+injectIndex*128

    #injectTime = random.randrange(0,runtime)
    #injectTime = 9841886
    #injectLoc = 65
    f = open(str(bench) + "/val_" + str(injectArch)+"_"+str(start)+"_"+str(end)+".txt", 'a')
    s = open(str(bench) + "/sec_" + str(injectArch)+"_"+str(start)+"_"+str(end)+".txt", 'a')

    f.write(str(injectTime) + "\t" + str(injectLoc) + "\t")

    if (injectArch == "Reg"):
        if(bench == 'susan') or (bench == 'jpeg'):
            os.system("./inject_output.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + str(i).zfill(5) + " " + gem5_binary + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i))
        else:
            os.system("./inject.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + gem5_binary + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i))
            
        non_failure = False
        fi_read = file(bench+"/FI_" + str(injectArch)+ "_" + str(i))
        for line in fi_read:
            if "NF" in line:
                non_failure = True

        previous = "NF"
        
        read = False
        contRead = False
        overwritten = False
                
        fi_read = file(bench+"/"+injectArch+"/FI_"+str(i))
        for line in fi_read:
            line2 = line.strip().split(' ')
            if "Corrupted" in line:
                if "read" in line and read is False:
                    read = True
                    if("syscall" not in line):
                        pcState = line2[9]
                elif "read" in line and read is True:
                    contRead = True
        
        failure = True
        stat_read = file(bench+"/"+injectArch+"/stats_" + str(i))
        for line in stat_read:
            pattern = re.compile(r'\s+')
            line = re.sub(pattern, '', line)
            line2 = line.strip().split(' ')
            if "sim_ticks" in line:
                sim_ticks = int(re.findall('\d+', line)[0])
                failure = False
                if(float(sim_ticks)/runtime*100 <= 100 and non_failure is True):
                    contRead = False
                elif(float(sim_ticks)/runtime*100 >= 200):
                    previous = "infinite"
                elif(float(sim_ticks)/runtime*100 > 100 and non_failure is True):
                    previous = "timing"
                
        if(failure):
            previous = "halt"
        elif(failure is False and non_failure is False):
            previous = "sdc"

        contReadIdx = 0
        second_complete = False
        read = False
        correctTime = []

        if(contRead):
            s.write(str(i)+"\n")
            fi_read = file(bench+"/"+injectArch+"/FI_"+str(i))
            linecount = 0
            previous_op = "ND"
            for line in fi_read:
                line2 = line.strip().split(':')
                line3 = line.strip().split(' ')
                if "read" in line:
                    if previous_op != line3[8]:
                        correctTime.append(line2[0])
                        previous_op = line3[8]
                        linecount += 1
                    else:
                        correctTime[linecount-1] = line2[0]
            #print correctTime
                
            if linecount == 1:
                root = previous_op
            
            else:
                #fi_read = file(bench+"/"+injectArch+"/FI_"+str(i))
                #for line in fi_read:
                print "Second-level analysis"
                for contReadIdx in range(0, linecount):    
                    #line2 = line.strip().split(':')
                    #line3 = line.strip().split(' ')
                    #if "read" in line:
                        #correctTime = line2[0]
                    if(bench == 'susan') or (bench == 'jpeg'):
                        os.system("./second_output.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + str(i).zfill(5) + " " + str(contReadIdx) +  " " + str(correctTime[contReadIdx]) + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i) + "_" + str(contReadIdx))
                    else:
                        os.system("./second.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) +  " " + str(contReadIdx) +  " " + str(correctTime[contReadIdx]) + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i) + "_" + str(contReadIdx))
                    
                    fi_read_second = file(bench+"/FI_" + str(injectArch)+ "_" + str(i) + "_" + str(contReadIdx))
                    for line_second in fi_read_second:
                        if "NF" in line_second:
                            non_failure = True
                            s.write("NF\t")
                        else:
                            second_complete = True
                            non_failure = False
                            s.write("F\t")
                    
                    root_candidate = "ND"
                            
                    fi_read_second = file(bench+"/"+injectArch+"/FI_"+str(i)+"_"+str(contReadIdx))
                    for line_second in fi_read_second:
                        line2_second = line_second.strip().split(' ')
                        if "Corrupted" in line_second:
                            if "read" in line_second and read is False:
                                read = True
                                s.write(line2_second[8] + "\t")
                                root_candidate = line2_second[8]
                            elif "read" in line_second and read is True:
                                s.write(line2_second[8] + "\t")
                                root_candidate = line2_second[8]
                            elif "overwritten" in line_second and read is False:
                                s.write("overwritten\t" + line2_second[4] + "\t" + line2_second[8] + "\t")
                            elif "unused" in line_second:
                                s.write("unused\t" + line2_second[4] + "\t\t")
                            
                    failure = True
                    stat_read = file(bench+"/"+injectArch+"/stats_" + str(i)+"_"+str(contReadIdx))
                    root = "ND"
                    for line in stat_read:
                        pattern = re.compile(r'\s+')
                        line = re.sub(pattern, '', line)
                        line2 = line.strip().split(' ')
                        if "sim_ticks" in line:
                            sim_ticks = int(re.findall('\d+', line)[0])
                            s.write(str(float(sim_ticks)/runtime*100) + "\n")
                            failure = False
                            if(float(sim_ticks)/runtime*100 >= 200):
                                if(previous == "infinite"):
                                    root = root_candidate
                            elif(float(sim_ticks)/runtime*100 > 100 and non_failure is True):
                                if(previous == "timing"):
                                    root = root_candidate
                            
                    if(failure):
                        s.write("failure\n")
                        if(previous == "halt"):
                            root = root_candidate
                    elif(failure is False and non_failure is False):
                        if(previous == "sdc"):
                            root = root_candidate
                        
                    #contReadIdx += 1
                    
                    if (root != "ND"):
                        s.write("\n")
                        break
    
        fi_read = file(bench+"/FI_" + str(injectArch)+ "_" + str(i))
        for line in fi_read:
            if "NF" in line:
                f.write("NF\t")
                non_failure = True
            else:
                f.write("F\t")

        fi_read = file(bench+"/"+injectArch+"/FI_"+str(i))
        for line in fi_read:
            line2 = line.strip().split(' ')
            if "Corrupted" in line:
                if "read" in line and contRead is False:
                    read = True
                    f.write("read\t" + line2[4] + "\t" + line2[8] + "\t")
                    break
                elif "read" in line and contRead is True:
                    contRead = True
                    f.write("read\t" + line2[4] + "\t" + root + "\t")
                    break
                elif "overwritten" in line and read is False:
                    f.write("overwritten\t" + line2[4] + "\t" + line2[8] + "\t")
                elif "unused" in line:
                    f.write("unused\t" + line2[4] + "\t\t")
                elif "corrected" in line:
                    f.write("corrected\t" + line2[4] + "\t\t")
        
        failure = True
        stat_read = file(bench+"/"+injectArch+"/stats_" + str(i))
        for line in stat_read:
            pattern = re.compile(r'\s+')
            line = re.sub(pattern, '', line)
            line2 = line.strip().split(' ')
            if "sim_ticks" in line:
                sim_ticks = int(re.findall('\d+', line)[0])
                f.write(str(float(sim_ticks)/runtime*100) + "\t")
                failure = False
                if(float(sim_ticks)/runtime*100 <= 100 and non_failure is True):
                    contRead = False
                
        if(failure):
            f.write("failure\t")
        
        incBranch = False
        logical = False
        shift = False
        dd = False
        cmp = False
        cond = False
        flag = False
        correct = False
        branch = False
        mult = False
        etc = False
                
        fi_read = file(bench+"/"+injectArch+"/FI_"+str(i))
        for line in fi_read:
            if "Incorrect branch" in line:
                incBranch = True
            elif "masked" in line and "DD" in line:
                dd = True
            elif "masked" in line and ("cmps" in line or "cmns" in line or "compare" in line):
                cmp = True
            elif "masked" in line and ("ASR" in line or "LSL" in line or "LSR" in line or "ROR" in line or "RRX" in line):
                shift = True
            elif "masked" in line and ("and" in line or "orr" in line):
                logical = True
            elif "masked" in line and ("conditional" in line):
                cond = True
            elif "masked" in line and ("flag" in line):
                cond = True
            elif "masked" in line and ("bl" in line):
                branch = True
            elif "masked" in line and ("mull" in line or "mla" in line):
                mult = True
            elif "corrected by memory instruction" in line:
                correct = True
            elif "masked" in line:
                etc = True
                line3 = line.strip().split(' ')
                print line3
        
        if(incBranch):
            f.write("incorrect branch\t")
        else:
            f.write("\t")
        if(dd):
            f.write("dynamically dead\t")
        else:
            f.write("\t")
        if(cmp):
            f.write("compare\t")
        else:
            f.write("\t")
        if(logical):
            f.write("logical\t")
        else:
            f.write("\t")
        if(shift):
            f.write("shift\t")
        else:
            f.write("\t")
        if(mult):
            f.write("multiply\t")
        else:
            f.write("\t")
        if(cond):
            f.write("conditional execution\t")
        else:
            f.write("\t")
        if(branch):
            f.write("store link regiter\t")
        else:
            f.write("\t")
        if(correct):
            f.write("corrected\t")
        else:
            f.write("\t")
        if(etc):
            f.write("etc\n")
        else:
            f.write("\t\n")
            
        #os.system("rm -rf " + bench + "/" + injectArch + "/FI_" + str(i) + "_*")
        #os.system("rm -rf " + bench + "/" + injectArch + "/FI_" + str(i))
        #os.system("rm -rf " + bench + "/" + injectArch + "/result_" + str(i) + "_*")
        #os.system("rm -rf " + bench + "/" + injectArch + "/simout_" + str(i) + "_*")
        #os.system("rm -rf " + bench + "/" + injectArch + "/simerr_" + str(i) + "_*")
        #os.system("rm -rf " + bench + "/" + "/FI_" + injectArch + "_" + str(i) + "_*")
            
            
    if (injectArch == "FU"):
        if(bench == 'susan') or (bench == 'jpeg'):
            os.system("./inject_output.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + str(i).zfill(5)  + " " + gem5_binary + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i))
        else:
            os.system("./inject.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + gem5_binary + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i))
        
        fi_read = file(bench+"/FI_" + str(injectArch)+ "_" + str(i))
        for line in fi_read:
            if "NF" in line:
                f.write("NF\t")
            else:
                f.write("F\t")
                
        fi_read = file(bench+"/"+injectArch+"/FI_"+str(i))
        for line in fi_read:
            line2 = line.strip().split(' ')
            if "Flipping" in line:
                f.write(line2[6] + "\t" + line2[9] + "\t")
        
        failure = True
        stat_read = file(bench+"/"+injectArch+"/stats_" + str(i))
        for line in stat_read:
            pattern = re.compile(r'\s+')
            line = re.sub(pattern, '', line)
            line2 = line.strip().split(' ')
            if "sim_ticks" in line:
                sim_ticks = int(re.findall('\d+', line)[0])
                f.write(str(float(sim_ticks)/runtime*100) + "\n")
                failure = False
                
        if(failure):
            f.write("failure\n")        

        if (injectArch == "LSQ"):
                if(bench == 'susan') or (bench == 'jpeg'):
                        os.system("./inject_output.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + str(i).zfill(5)  + " " + gem5_binary + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i))
                else:
                        os.system("./inject.sh " + str(arch) + " " + str(bench) + " " + str(injectTime) + " " + str(injectLoc) + " " + str(i) + " " + str(injectArch) + " " + str(2*runtime) + " " + gem5_binary + " > " + str(bench) + "/FI_" + str(injectArch) + "_" + str(i))

                fi_read = file(bench+"/FI_" + str(injectArch)+ "_" + str(i))
                for line in fi_read:
                        if "NF" in line:
                                f.write("NF\t")
                        else:
                                f.write("F\t")

                failure = True
                stat_read = file(bench+"/"+injectArch+"/stats_" + str(i))
                for line in stat_read:
                        pattern = re.compile(r'\s+')
                        line = re.sub(pattern, '', line)
                        line2 = line.strip().split(' ')
                        if "sim_ticks" in line:
                                sim_ticks = int(re.findall('\d+', line)[0])
                                f.write(str(float(sim_ticks)/runtime*100) + "\n")
                                failure = False

                if(failure):
                        f.write("failure\n")

        f.close()
        s.close()
