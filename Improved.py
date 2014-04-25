import sys
import scipy
import collections
import cPickle
from time import time
t = time()

class Alignment(object):
    def __init__(self):
        #
        self.url_e = 'corpus.en'
        self.url_f = 'corpus.es'
        self.url_a = 'alignments.txt'
        self.url_dev_e = 'dev.en'
        self.url_dev_f = 'dev.es'
        self.url_dev_out = 'dev.out'
        self.pick = 'IBM1.pick'
        
        self.iterations = 10
        self.iter = 0
        self.infinitesimal = 0.0000001
        
        # Parameters tuning
        self.nullprob = 0.1
        self.dir = 0.0


        # initialization for the docs
        self.wordmap_e = {}
        self.wordmap_f = {}
        self.words_e = []
        self.words_f = []

        
        self.sum_s = 0 # size of sentences
        self.sum_e = 0
        self.sum_f = 0

        # used in inference
        self.sentences_e = []
        self.sentences_f = []
        self.lengths_e = []
        self.lengths_f = []
        self.alignments = []

        # used in dev
        self.sentences_dev_e = []
        self.sentences_dev_f = []
        self.lengths_dev_e = []
        self.lengths_dev_f = []
        self.alignments_dev = []
        
        # lengths value
        self.lenval_e = []
        self.lenval_f = []

        # counts
        self.count_e = collections.defaultdict(int)
        self.count_fe = collections.defaultdict(int)
        self.count_jilm = collections.defaultdict(int)
        self.count_ilm = collections.defaultdict(int)
        
        
        # delta
        self.delta = {}
        
        self.q = collections.defaultdict(lambda:self.infinitesimal) #distortion probability
        self.t = collections.defaultdict(lambda:self.infinitesimal) #translation probability


    def Inputcorpus(self):
        fin_e = open('corpus.en','r')
        for line in fin_e:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_e:
                    self.wordmap_e[word] = len(self.wordmap_e) # build wordmap
                    self.words_e.append(word) # save words
                self.count_e[word] += 1
                words_idx.append(self.wordmap_e[word])
            if len(words_idx) not in self.lenval_e: # restore all the length values
                self.lenval_e.append(len(words_idx))
            self.sentences_e.append(words_idx)
            self.lengths_e.append(len(words_idx))
            self.sum_s = len(self.sentences_e)# count sentence
        fin_e.close()
        fin_f = open('corpus.es','r')
        for line in fin_f:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_f:
                    self.wordmap_f[word] = len(self.wordmap_f) # build wordmap
                    self.words_f.append(word) # save words
                words_idx.append(self.wordmap_f[word])
            if len(words_idx) not in self.lenval_f: # restore all the length values
                self.lenval_f.append(len(words_idx))
            self.sentences_f.append(words_idx)
            self.lengths_f.append(len(words_idx))
        fin_f.close()
        print "Sentences:"+str(self.sum_s)
        print "E words:"+str(len(self.words_e))
        print "F words:"+str(len(self.words_f))

    def RandomiseAlignments(self):
        for s in xrange(0,self.sum_s):
            alignments = []
            for i in xrange(0,len(self.sentences_f[s])):
                alignments.append(0)
            self.alignments_f.append(alignments)
        

    #-----------------------------------------------PakageFunction-------------------------------------------#   
    def GetT(self,idx_f,idx_e):         #t(f|e)
        self.t.setdefault((idx_f,idx_e),1.0/len(self.wordmap_f))
        return self.t[(idx_f,idx_e)]
    
    def GetQ_IBM2(self,j,i,l,m):             #q(j|i,l,m)
        return self.q[(j,i,l,m)]

    def GetQ_IBM1(self,j,i,l,m):             #q(j|i,l,m)
        return 1.0/(l+1)
        
    def GetDelta(self,s,i,j):
        return self.delta[(s,i,j)]
    
    def GetCount_fe(self,idx_f,idx_e):
        return self.count_fe[(idx_f,idx_e)]

    def GetCount_e(self,idx_e):
        return self.count_e[idx_e]
    
    def GetCount_jilm(self,j,i,l,m):
        return self.count_jilm[(j,i,l,m)]
    
    def GetCount_ilm(self,i,l,m):
        return self.count_ilm[(i,l,m)]
    '''
    def GetCount_fe(self,idx_f,idx_e):
        if (idx_f,idx_e) in self.count_fe:
            return self.count_fe[(idx_f,idx_e)]
        else:
            return self.infinitesimal
    def GetCount_e(self,idx_e):
        if idx_e in self.count_e:
            return self.count_e[idx_e]
        else:
            return self.infinitesimal
    def GetCount_jilm(self,j,i,l,m):
        if (j,i,l,m) in self.count_jilm:
            return self.count_jilm[(j,i,l,m)]
        else:
            return self.infinitesimal
    def GetCount_ilm(self,i,l,m):
        if (i,l,m) in self.count_ilm:
            return self.count_ilm[(i,l,m)]
        else:
            return self.infinitesimal
    '''    


    #-----------------------------------------------ComputeFunction-------------------------------------------#
    
    def InitT(self):
        for idx_f in xrange(0,len(self.wordmap_f)):
            self.t[(idx_f,-1)]=1.0/len(self.wordmap_f)
            #self.t[(idx_f,-1)]=self.nullprob
    
    def ComputeT(self):
        #self.t = {}
        for (idx_f,idx_e),val in self.count_fe.iteritems():
            self.t[(idx_f,idx_e)] = self.GetCount_fe(idx_f,idx_e)/self.GetCount_e(idx_e)
            
            
    def ComputeQ_IBM2(self):
        for l in self.lenval_e:
            for m in self.lenval_f:
                for i in xrange(0,m):
                    #for j in xrange(0,l):
                    #    self.q[(j,i,l,m)]=self.GetCount_jilm(j,i,l,m)*1.0/self.GetCount_ilm(i,l,m)   # if no?
                    #'''
                    normalisation = self.GetCount_ilm(i,l,m)
                    if normalisation == 0:
                        for j in xrange(-1,l):
                            self.q[(j,i,l,m)] = self.infinitesimal
                            #print "Issue: self.GetCount_ilm(i,l,m)==0"
                    else:
                        for j in xrange(-1,l):
                            self.q[(j,i,l,m)]=self.GetCount_jilm(j,i,l,m)*1.0/normalisation   # if no?
                    #'''
        
    def ComputeDelta_IBM1(self):
        for s in xrange(0,self.sum_s):
            if s%1000 == 0:
                print "E-step - ComputeDelta - Sentence:"+str(s)
            m = len(self.sentences_f[s])
            l = len(self.sentences_e[s])
            for i in xrange(0,m):
                #print "TMP prob:"
                normalization = 0
                for j in xrange(0,l):
                    normalization = normalization + self.GetT(self.sentences_f[s][i],self.sentences_e[s][j])*(1-self.nullprob)
                normalization += self.GetT(self.sentences_f[s][i],-1)*self.nullprob    
                for j in xrange(0,l):
                    self.delta[(s,i,j)] = self.GetT(self.sentences_f[s][i],self.sentences_e[s][j])*(1-self.nullprob)/normalization
                #    print self.delta[(s,i,j)]
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" Delta:"+str(self.delta[(s,i,j)])
                #nullAlignment
                self.delta[(s,i,-1)] = self.GetT(self.sentences_f[s][i],-1)*self.nullprob/normalization
                #print self.delta[(s,i,-1)]

                
    def UpdateCounts_IBM1(self):
        self.count_e.clear()
        self.count_fe.clear() # define a new counts in every iteration
        for s in xrange(0,self.sum_s):
            if s%1000 == 0:
                print "E-step- Updating Counts - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            for i in xrange(0,m):
                for j in xrange(0,l):
                    # Count C(e,f)
                    self.count_fe[(self.sentences_f[s][i],self.sentences_e[s][j])] += self.GetDelta(s,i,j)
                    # Count C(e)
                    self.count_e[self.sentences_e[s][j]] += self.GetDelta(s,i,j)
                # nullAlignment
                self.count_fe[(self.sentences_f[s][i],-1)] += self.GetDelta(s,i,-1)
                self.count_e[-1] += self.GetDelta(s,i,-1)
    def ComputeDelta_IBM2(self):
        fout = open('delta_'+str(self.iter),'w')           
        for s in xrange(0,self.sum_s):
            if s%1000 == 0:
                print "E-step - ComputeDelta - Sentence:"+str(s)
            m = len(self.sentences_f[s])
            l = len(self.sentences_e[s])
            fout.write( "Sentence: "+str(s) + " Alignement-------" + '\n')
            for i in xrange(0,m):
                normalization = 0
                p_pos = 0
                p_max = 0
                for j in xrange(0,l):
                    p_tmp = self.GetT(self.sentences_f[s][i],self.sentences_e[s][j])*self.GetQ_IBM2(j,i,l,m)*(1-self.nullprob)
                    normalization += p_tmp
                    if p_tmp >=p_max:
                        p_pos = j
                        p_max = p_tmp
                p_tmp = self.GetT(self.sentences_f[s][i],-1)*self.nullprob
                normalization += p_tmp
                if p_tmp >=p_max:
                    p_pos = -1
                if p_pos == -1:
                    for x in xrange(0,l):
                        fout.write(" - ")
                else:
                    for x in xrange(0,p_pos):
                        fout.write(' - ')
                    fout.write(' * ')
                    for x in xrange(p_pos+1,l):
                        fout.write(' - ')
                fout.write('  '+ str(p_pos) +'\n')
                for j in xrange(0,l):
                    self.delta[(s,i,j)] = self.GetT(self.sentences_f[s][i],self.sentences_e[s][j])*self.GetQ_IBM2(j,i,l,m)*(1-self.nullprob)/normalization
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" Delta:"+str(self.delta[(s,i,j)])
                #nullAlignment
                self.delta[(s,i,-1)] = self.GetT(self.sentences_f[s][i],-1)*self.nullprob/normalization
        fout.close()
    def UpdateCounts_IBM2(self):
        self.count_e.clear()
        self.count_fe.clear() # define a new counts in every iteration
        self.count_jilm.clear()
        self.count_ilm.clear()
        for s in xrange(0,self.sum_s):
            if s%1000 == 0:
                print "E-step- Updating Counts - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            for i in xrange(0,m):
                for j in xrange(0,l):
                    # Count C(e,f)
                    self.count_fe[(self.sentences_f[s][i],self.sentences_e[s][j])] += self.GetDelta(s,i,j)
                    # Count C(e)
                    self.count_e[self.sentences_e[s][j]] += self.GetDelta(s,i,j)
                    # Count C(j,i,l,m)
                    self.count_jilm[(j,i,l,m)] += self.GetDelta(s,i,j)
                    # Count C(i,l,m)
                    self.count_ilm[(i,l,m)] += self.GetDelta(s,i,j)
                # nullAlignment
                self.count_fe[(self.sentences_f[s][i],-1)] += self.GetDelta(s,i,-1)
                self.count_e[-1] += self.GetDelta(s,i,-1)
                self.count_jilm[(-1,i,l,m)] += self.GetDelta(s,i,-1)
                self.count_ilm[(i,l,m)] += self.GetDelta(s,i,-1)
    #def IBM1(self):
    #-----------------------------------------------Decoding-------------------------------------------# 
    def GetAlignments_IBM1(self):
        self.alignments = []
        for s in xrange(0,self.sum_s):
            if s%1000 == 0:
                print "Decoding- Alignments - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            self.alignments.append([])
            for i in xrange(0,m):
                self.alignments[s].append(0)
                maximum = 0
                for j in xrange(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM1(j,i,l,m))
                    tmp = self.GetT(self.sentences_f[s][i],self.sentences_e[s][j])*self.GetQ_IBM1(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp  >= maximum:
                        self.alignments[s][i] = j
                        maximum = tmp
                tmp = self.GetT(self.sentences_f[s][i],-1)*self.GetQ_IBM2(-1,i,l,m) # nullAlignment
                if tmp >= maximum:
                    self.alignments[s][i] = -1
        fout = open(self.url_a,'w')
        for s in xrange(0,self.sum_s):
            fout.write(str(self.alignments[s]))
            fout.write('\n')
        fout.close()

    def GetAlignments_IBM2(self):
        self.alignments = []
        for s in xrange(0,self.sum_s):
            if s%1000 == 0:
                print "Decoding- Alignments - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            self.alignments.append([])
            for i in xrange(0,m):
                self.alignments[s].append(0)
                maximum = 0
                for j in xrange(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM2(j,i,l,m))
                    tmp = self.GetT(self.sentences_f[s][i],self.sentences_e[s][j])*self.GetQ_IBM2(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp >= maximum:
                        self.alignments[s][i] = j
                        maximum = tmp
                tmp = self.GetT(self.sentences_f[s][i],-1)*self.GetQ_IBM2(-1,i,l,m) # nullAlignment
                if tmp >= maximum:
                    self.alignments[s][i] = -1
        fout = open(self.url_a,'w')
        for s in xrange(0,self.sum_s):
            fout.write(str(self.alignments[s]))
            fout.write('\n')
        fout.close()        
    
    # initialise delta
    def EM_IBM1(self):
        
        # Initial E-step
        self.InitT()
                              
        for self.iter in xrange(0,self.iterations):
            print "EM processing in iteration:"+str(self.iter)
        #E-step
            print "E-step-Computing Delta."
            self.ComputeDelta_IBM1()
            print "E-step-UpdateCounts."
            self.UpdateCounts_IBM1()
            
        #M-step
             # compute t
            print "M-step-ComputeT."
            self.ComputeT()
             # compute q  j i l m
            #self.ComputeQ_IBM1()

            
    def EM_IBM2(self):
        
        # Initial E-step
        self.InitT()
                              
        for self.iter in xrange(0,self.iterations):
            print "EM processing in iteration:"+str(self.iter)
        #E-step
            print "E-step-Computing Delta."
            if self.iter >=5:
                self.ComputeDelta_IBM2()
            else:
                self.ComputeDelta_IBM1()
            print "E-step-UpdateCounts."
            self.UpdateCounts_IBM2()
            
        #M-step
             # compute t
            print "M-step-ComputeT."
            self.ComputeT()
             # compute q  j i l m
            if self.iter >=5:
                print "M-step-ComputeQ"
                self.ComputeQ_IBM2()
            

    def Dev_IBM1(self):
        fin_e = open(self.url_dev_e,'r')
        for line in fin_e:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_e:
                    words_idx.append(-1)
                else:
                    words_idx.append(self.wordmap_e[word])
            self.sentences_dev_e.append(words_idx)
            self.lengths_dev_e.append(len(words_idx))
            
        fin_f = open(self.url_dev_f,'r')
        for line in fin_f:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_f:
                    words_idx.append(-1)
                else:
                    words_idx.append(self.wordmap_f[word])        
            self.sentences_dev_f.append(words_idx)
            self.lengths_dev_f.append(len(words_idx))
            
        # get alignments for dev
        self.alignments_dev = []
        for s in xrange(0,len(self.sentences_dev_e)):
            if s%1000 == 0:
                print "DEV- Alignments - Sentence:"+str(s)
            m = self.lengths_dev_f[s]
            l = self.lengths_dev_e[s]
            self.alignments_dev.append([])
            for i in xrange(0,m):
                self.alignments_dev[s].append(0)
                maximum = 0
                if self.sentences_dev_f[s][i] == -1: #filter the words which are not in wordmap
                    self.alignments_dev[s][i] = -1
                    continue
                for j in xrange(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM2(j,i,l,m))
                    tmp = self.GetT(self.sentences_dev_f[s][i],self.sentences_dev_e[s][j])#*self.GetQ_IBM1(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp  >= maximum:
                        self.alignments_dev[s][i] = j
                        maximum = tmp
                # nullAlignment
                # Compare to "null alignemnt probablity"
                #'''
                tmp = self.GetT(self.sentences_dev_f[s][i],-1) # nullAlignment
                if tmp >= maximum:
                    self.alignments_dev[s][i] = -1
                #'''
        fout = open(self.url_dev_out,'w')
        for s in xrange(0,len(self.sentences_dev_e)):
            for i in xrange(0,len(self.alignments_dev[s])):
                if self.alignments_dev[s][i] ==-1:
                    continue
                fout.write(str(s+1)+' '+str(self.alignments_dev[s][i]+1)+' '+str(i+1))
                fout.write('\n')
        fout.close()
        
    def Dev_IBM2(self):
        fin_e = open(self.url_dev_e,'r')
        for line in fin_e:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_e:
                    words_idx.append(-2)            #-1 is null alignment
                else:
                    words_idx.append(self.wordmap_e[word])
            self.sentences_dev_e.append(words_idx)
            self.lengths_dev_e.append(len(words_idx))
            
        fin_f = open(self.url_dev_f,'r')
        for line in fin_f:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_f:
                    words_idx.append(-2)
                else:
                    words_idx.append(self.wordmap_f[word])        
            self.sentences_dev_f.append(words_idx)
            self.lengths_dev_f.append(len(words_idx))
            
        # get alignments for dev
        self.alignments_dev = []
        for s in xrange(0,len(self.sentences_dev_e)):
            m = self.lengths_dev_f[s]
            l = self.lengths_dev_e[s]
            self.alignments_dev.append([])
            for i in xrange(0,m):
                self.alignments_dev[s].append(0)
                maximum = 0
                if self.sentences_dev_f[s][i] == -2: #filter the French words which are not in wordmap
                    self.alignments_dev[s][i] = -1
                    continue
                #print 'TMP prob:'
                for j in xrange(0,l):    # starts from 1
                    
                    if self.sentences_dev_e[s][j] == -2: #filter the English words which are not in wordmap
                        continue                    
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM2(j,i,l,m))
                    tmp = self.GetT(self.sentences_dev_f[s][i],self.sentences_dev_e[s][j])*self.GetQ_IBM1(j,i,l,m)
                    if tmp  >= maximum:
                        self.alignments_dev[s][i] = j
                        maximum = tmp   
                # nullAlignment
                # Compare to "null alignemnt probablity"
                tmp = self.GetT(self.sentences_dev_f[s][i],-1)*self.GetQ_IBM2(-1,i,l,m) # nullAlignment
                #print tmp
                if tmp >= maximum:
                    self.alignments_dev[s][i] = -1
        print "\n DEV- Alignments - Sentence:"+str(s)
        fout = open(self.url_dev_out,'w')
        fout_align = open('dev.alignment','w')
        for s in xrange(0,len(self.sentences_dev_e)):
            fout_align.write('Dev Sentence: '+str(s)+'\n')
            for i in xrange(0,len(self.alignments_dev[s])):
                if self.alignments_dev[s][i] ==-1:
                    for x in xrange(0,len(self.sentences_dev_e[s])):
                        fout_align.write(' - ')
                    continue
                for x in xrange(0,self.alignments_dev[s][i]):
                    fout_align.write(' - ')
                fout_align.write(' * ')
                for x in xrange(self.alignments_dev[s][i]+1,len(self.sentences_dev_e[s])):
                    fout_align.write(' - ')
                fout_align.write(' '+str(self.alignments_dev[s][i])+'\n')
                fout.write(str(s+1)+' '+str(self.alignments_dev[s][i]+1)+' '+str(i+1))
                fout.write('\n')
        fout.close()
        fout_align.close()

myAlignment = Alignment()
myAlignment.Inputcorpus()
myAlignment.EM_IBM2()

#myAlignment.Print()
#myAlignment.GetAlignments_IBM1()
myAlignment.Dev_IBM2()
print "total run time:"
print time()-t


