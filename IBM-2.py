import sys
import scipy
import collections

class Alignment(object):
    def __init__(self):
        #
        self.url_e = 'corpus.en'
        self.url_f = 'corpus.es'
        self.url_a = 'alignments.txt'
        self.url_dev_e = 'dev.en'
        self.url_dev_f = 'dev.es'
        self.url_dev_out = 'dev.out'
        self.iterations = 20
        self.infinitesimal = 0.0000001
        
        # Parameters tuning
        self.nullalignment = 0.0
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
        self.count_e = {}
        self.count_ef = {}
        self.count_jilm = {}
        self.count_ilm = {}
        
        
        # delta
        self.delta = {}
        
        self.q = {} #distortion probability
        self.t = {} #translation probability
        self.updated_t = {}

    def Inputcorpus(self):
        fin_e = open('corpus.en','r')
        for line in fin_e:
            words = line.strip().split()
            words_idx = []
            for word in words:
                if word not in self.wordmap_e:
                    self.wordmap_e[word] = len(self.wordmap_e) # build wordmap
                    self.words_e.append(word) # save words
                    self.count_e[word] = 1
                else:
                    self.count_e[word] = self.count_e[word]+1
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
        for s in range(0,self.sum_s):
            alignments = []
            for i in range(0,len(self.sentences_f[s])):
                alignments.append(0)
            self.alignments_f.append(alignments)
        
    #def ComputDelta(self):

    #def ComputCounts(self):
    #-----------------------------------------------PakageFunction-------------------------------------------#   
    def GetT(self,idx_e,idx_f):         #t(e|f)
        if (idx_e,idx_f) in self.t:
            return self.t[(idx_e,idx_f)]
        else:
            return self.infinitesimal
    def GetQ_IBM2(self,j,i,l,m):             #q(j|i,l,m)
        if (j,i,l,m) in self.q:
            return self.q[(j,i,l,m)]
        else:
            return self.infinitesimal
    def GetQ_IBM1(self,j,i,l,m):             #q(j|i,l,m)
            return 1.0/(l+1)

    def GetCount_ef(self,idx_e,idx_f):
        if (idx_e,idx_f) in self.count_ef:
            return self.count_ef[(idx_e,idx_f)]
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
    def GetDelta(self,s,i,j):
        if (s,i,j) in self.delta:
            return self.delta[(s,i,j)]
        else:
            return self.infinitesimal
    #-----------------------------------------------ComputeFunction-------------------------------------------#  
    def ComputeT(self):
        '''
        for idx_e in range(0,len(self.words_e)):
            for idx_f in range(0,len(self.words_f)):
                self.t[(idx_e,idx_f)]=self.GetCount_ef(idx_e,idx_f)/self.GetCount_e(idx_e)*1.0+0.0001    #   Count_e == 0?
        '''
        self.t = {}
        for (idx_e,idx_f),val in self.count_ef.iteritems():
            #print "idx_e:"+str(idx_e)+" idx_f"+str(idx_f)
            self.t[(idx_e,idx_f)] = self.GetCount_ef(idx_e,idx_f)*1.0/self.GetCount_e(idx_e)
            #print "EF:"+str(self.GetCount_ef(idx_e,idx_f))+" E:"+str(self.GetCount_e(idx_e))
    def ComputeQ_IBM2(self):
        for l in self.lenval_e:
            for m in self.lenval_f:
                for j in range(0,l):
                    for i in range(0,m):
                        if self.GetCount_ilm(i,l,m)==0:
                            self.q[(j,i,l,m)] = self.infinitesimal
                            print "Issue: self.GetCount_ilm(i,l,m)==0"
                        else:
                            self.q[(j,i,l,m)]=self.GetCount_jilm(j,i,l,m)*1.0/self.GetCount_ilm(i,l,m)   # if no?
        
    def InitialiseT(self):
        for idx_e in range(0,len(self.words_e)):
            for idx_f in range(0,len(self.words_f)):
                self.t[(idx_e,idx_f)]=1/len(self.words_e)*1.0
                print "T- e:"+str(idx_e)+" f:"+str(idx_f)
    def ComputeDelta_IBM1(self):
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "E-step - ComputeDelta - Sentence:"+str(s)
            m = len(self.sentences_f[s])
            l = len(self.sentences_e[s])
            for i in range(0,m):
                normalization = 0
                for j in range(0,l):
                    normalization = normalization + self.GetT(self.sentences_e[s][j],self.sentences_f[s][i])
                for j in range(0,l):
                    self.delta[(s,i,j)] = self.GetT(self.sentences_e[s][j],self.sentences_f[s][i])/normalization
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" Delta:"+str(self.delta[(s,i,j)])

    def UpdateCounts_IBM1(self):
        self.count_e = {}
        self.count_ef = {} # define a new counts in every iteration
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "M-step- Updating Counts - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            for i in range(0,m):
                for j in range(0,l):
                    # Count C(e,f)
                    if (self.sentences_e[s][j],self.sentences_f[s][i]) in self.count_ef:
                        self.count_ef[(self.sentences_e[s][j],self.sentences_f[s][i])] = \
                            self.count_ef[(self.sentences_e[s][j],self.sentences_f[s][i])]+self.GetDelta(s,i,j)
                    else:
                        self.count_ef[(self.sentences_e[s][j],self.sentences_f[s][i])] = self.GetDelta(s,i,j)
                    # Count C(e)
                    if self.sentences_e[s][j] in  self.count_e:
                        self.count_e[self.sentences_e[s][j]] = self.count_e[self.sentences_e[s][j]] + self.GetDelta(s,i,j)
                    else:
                        self.count_e[self.sentences_e[s][j]] = self.GetDelta(s,i,j)

    def ComputeDelta_IBM2(self):
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "E-step - ComputeDelta - Sentence:"+str(s)
            m = len(self.sentences_f[s])
            l = len(self.sentences_e[s])
            for i in range(0,m):
                normalization = 0
                for j in range(0,l):
                    normalization = normalization + self.GetT(self.sentences_e[s][j],self.sentences_f[s][i])*self.GetQ_IBM2(j,i,l,m)
                for j in range(0,l):
                    self.delta[(s,i,j)] = self.GetT(self.sentences_e[s][j],self.sentences_f[s][i])*self.GetQ_IBM2(j,i,l,m)/normalization
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" Delta:"+str(self.delta[(s,i,j)])

    def UpdateCounts_IBM2(self):
        self.count_e = {}
        self.count_ef = {} # define a new counts in every iteration
        self.count_jilm = {}
        self.count_ilm = {}
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "M-step- Updating Counts - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            for i in range(0,m):
                for j in range(0,l):
                    # Count C(e,f)
                    if (self.sentences_e[s][j],self.sentences_f[s][i]) in self.count_ef:
                        self.count_ef[(self.sentences_e[s][j],self.sentences_f[s][i])] = \
                            self.count_ef[(self.sentences_e[s][j],self.sentences_f[s][i])]+self.GetDelta(s,i,j)
                    else:
                        self.count_ef[(self.sentences_e[s][j],self.sentences_f[s][i])] = self.GetDelta(s,i,j)
                    # Count C(e)
                    if self.sentences_e[s][j] in  self.count_e:
                        self.count_e[self.sentences_e[s][j]] = self.count_e[self.sentences_e[s][j]] + self.GetDelta(s,i,j)
                    else:
                        self.count_e[self.sentences_e[s][j]] = self.GetDelta(s,i,j)
                    # Count C(j,i,l,m)
                    if (j,i,l,m) in self.count_jilm:
                        self.count_jilm[(j,i,l,m)] = self.count_jilm[(j,i,l,m)] + self.GetDelta(s,i,j)
                    else:
                        self.count_jilm[(j,i,l,m)] = self.GetDelta(s,i,j)
                    # Count C(i,l,m)
                    if (i,l,m) in self.count_ilm:
                        self.count_ilm[(i,l,m)] = self.count_ilm[(i,l,m)] + self.GetDelta(s,i,j)
                    else:
                        self.count_ilm[(i,l,m)] = self.GetDelta(s,i,j)
    #def IBM1(self):
    #-----------------------------------------------Decoding-------------------------------------------# 
    def GetAlignments_IBM1(self):
        self.alignments = []
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "Decoding- Alignments - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            self.alignments.append([])
            for i in range(0,m):
                self.alignments[s].append(0)
                maximum = 0
                for j in range(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM1(j,i,l,m))
                    tmp = self.GetT(self.sentences_e[s][j],self.sentences_f[s][i])*self.GetQ_IBM1(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp  >= maximum:
                        self.alignments[s][i] = j
                        maximum = tmp
        fout = open(self.url_a,'w')
        for s in range(0,self.sum_s):
            fout.write(str(self.alignments[s]))
            fout.write('\n')
        fout.close()

    def GetAlignments_IBM2(self):
        self.alignments = []
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "Decoding- Alignments - Sentence:"+str(s)
            m = self.lengths_f[s]
            l = self.lengths_e[s]
            self.alignments.append([])
            for i in range(0,m):
                self.alignments[s].append(0)
                maximum = 0
                for j in range(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM2(j,i,l,m))
                    tmp = self.GetT(self.sentences_e[s][j],self.sentences_f[s][i])*self.GetQ_IBM2(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp  >= maximum:
                        self.alignments[s][i] = j
                        maximum = tmp
        fout = open(self.url_a,'w')
        for s in range(0,self.sum_s):
            fout.write(str(self.alignments[s]))
            fout.write('\n')
        fout.close()        

    def EM_IBM1(self):
        
        # Initial E-step
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "Initial E-step - Sentence:"+str(s)
            m = len(self.sentences_f[s])
            l = len(self.sentences_e[s])
            for i in range(0,m):
                normalization = 0
                for j in range(0,l):
                    normalization = normalization + 1.0/len(self.words_e)
                for j in range(0,l):
                    self.delta[(s,i,j)] = (1.0/len(self.words_e))/normalization
        for it in range(0,self.iterations):
            print "EM processing in iteration:"+str(it)      
        #M-step
            print "M-step-UpdateCounts."
            self.UpdateCounts_IBM1()
             # compute t
            print "M-step-ComputeT."
            self.ComputeT()
             # compute q  j i l m
            #self.ComputeQ_IBM1()
        #E-step
            #if it == 0:
            #    print "Initialising Tanslation Probability T."
            #    self.InitialiseT()
            print "E-step-Computing Delta."
            self.ComputeDelta_IBM1()
            
    def EM_IBM2(self):
        
        # Initial E-step
        for s in range(0,self.sum_s):
            if s%1000 == 0:
                print "Initial E-step - Sentence:"+str(s)
            m = len(self.sentences_f[s])
            l = len(self.sentences_e[s])
            for i in range(0,m):
                normalization = 0
                for j in range(0,l):
                    normalization = normalization + 1.0/len(self.words_e)
                for j in range(0,l):
                    self.delta[(s,i,j)] = (1.0/len(self.words_e))/normalization
        for it in range(0,self.iterations):
            print "EM processing in iteration:"+str(it)      
        #M-step
            print "M-step-UpdateCounts."
            self.UpdateCounts_IBM2()
             # compute t
            print "M-step-ComputeT."
            self.ComputeT()
             # compute q  j i l m
            if it >=5:
                self.ComputeQ_IBM2()
        #E-step
            #if it == 0:
            #    print "Initialising Tanslation Probability T."
            #    self.InitialiseT()
            print "E-step-Computing Delta."
            if it >=5:
                self.ComputeDelta_IBM2()
            else:
                self.ComputeDelta_IBM1()

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
        for s in range(0,len(self.sentences_dev_e)):
            if s%1000 == 0:
                print "DEV- Alignments - Sentence:"+str(s)
            m = self.lengths_dev_f[s]
            l = self.lengths_dev_e[s]
            self.alignments_dev.append([])
            for i in range(0,m):
                self.alignments_dev[s].append(0)
                maximum = 0
                if self.sentences_dev_f[s][i] == -1: #filter the words which are not in wordmap
                    self.alignments_dev[s][i] = -1
                    continue
                for j in range(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM2(j,i,l,m))
                    tmp = self.GetT(self.sentences_dev_e[s][j],self.sentences_dev_f[s][i])#*self.GetQ_IBM1(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp  >= maximum:
                        self.alignments_dev[s][i] = j
                        maximum = tmp
                # Compare to "null alignemnt probablity"
                
        fout = open(self.url_dev_out,'w')
        for s in range(0,len(self.sentences_dev_e)):
            for i in range(0,len(self.alignments_dev[s])):
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
        for s in range(0,len(self.sentences_dev_e)):
            if s%1000 == 0:
                print "DEV- Alignments - Sentence:"+str(s)
            m = self.lengths_dev_f[s]
            l = self.lengths_dev_e[s]
            self.alignments_dev.append([])
            for i in range(0,m):
                self.alignments_dev[s].append(0)
                maximum = 0
                if self.sentences_dev_f[s][i] == -1: #filter the words which are not in wordmap
                    self.alignments_dev[s][i] = -1
                    continue
                for j in range(0,l):    # starts from 1
                    #tmp = scipy.log(self.GetT(self.sentences_e[s][j],self.sentences_f[s][i]))+scipy.log(self.GetQ_IBM2(j,i,l,m))
                    tmp = self.GetT(self.sentences_dev_e[s][j],self.sentences_dev_f[s][i])*self.GetQ_IBM1(j,i,l,m)
                    #print "s:"+str(s)+" i:"+str(i)+" j:"+str(j)+" logPro:"+str(tmp)
                    if j==0:
                        maximum = tmp               
                    #print "tmp:"+str(tmp)+" pre:"+str(pre)
                    if tmp  >= maximum:
                        self.alignments_dev[s][i] = j
                        maximum = tmp
        fout = open(self.url_dev_out,'w')
        for s in range(0,len(self.sentences_dev_e)):
            for i in range(0,len(self.alignments_dev[s])):
                if self.alignments_dev[s][i] ==-1:
                    continue
                fout.write(str(s+1)+' '+str(self.alignments_dev[s][i]+1)+' '+str(i+1))
                fout.write('\n')
        fout.close()     

myAlignment = Alignment()
myAlignment.Inputcorpus()
myAlignment.EM_IBM2()
#myAlignment.Print()
#myAlignment.GetAlignments_IBM1()
myAlignment.Dev_IBM2()



