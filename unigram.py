#!/usr/bin/env python
# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------#
# unsupervised_wordseg.py
# Wei Weng <wei.weng@pku.edu.cn>
# vim: ts=4 sw=4 sts=4 et tw=78:
#----------------------------------------------------------------------------#

import sys, os
import codecs
import bz2, gzip
import string 
import random
import re
#from tools.myutil import uprint

ALPHA = 2

def sopen(filename, mode='rb', encoding='utf8', errors='strict'):
    """ Transparently uses compression on the given file based on file
        extension.

        @param filename: The filename to use for the file handle.
        @param mode: The mode to open the file in, e.g. 'r' for read, 'w' for
            write, 'a' for append.
        @param encoding: The encoding to use. Can be set to None to avoid
            using unicode at all.
    """
    readMode = 'r' in mode
    if readMode and 'w' in mode:
        print(mode)
        #raise Exception, "Must be either read mode or write, but not both"

    if filename.endswith('.bz2'):
        stream = bz2.BZ2File(filename, mode)
    elif filename.endswith('.gz'):
        stream = gzip.GzipFile(filename, mode)
    elif filename == '-':
        if readMode:
            stream = sys.stdin
        else:
            stream = sys.stdout
    else:
        stream = open(filename, mode)
    
    if encoding not in (None, 'byte'):
        if readMode:
            return codecs.getreader(encoding)(stream, errors)
        else:
            return codecs.getwriter(encoding)(stream, errors)
    
    return stream




#----------------------------------------------------------------------------#
class uwseg:
    """
    进行无指导分词
    """
    def __init__(self,corpfile):
        """"
        """
  
        self.past_dict = dict()
        self.all_dict = dict()
        self.cfile = corpfile
        self.outfile = corpfile+'.us'
        self.startfile = corpfile+'.us0'
        #存储隐变量的列表 '1'是断开 ‘0’是连接
        self.flaglist=list()
        self.charlist = list()
        self.corpsize = 0
        self.charset = set()
        self.charsetsize = 0

    def storeresult(self,t=''):
        """
        根据隐变量的采样结果，输出分词结果
        """
        outstream = sopen(self.outfile+str(t),'w','utf-8')
        for i in range(self.corpsize-1):
            try:
                f = self.flaglist[i]
                c = self.charlist[i]
            except IndexError:
                print str(i)
            outstream.write(unicode(c))
            if(f==1):
                outstream.write(' ')
        c = self.charlist[i+1]
        outstream.write(c)

    def initcount(self):
        """
        """
        instream = sopen(self.startfile,'r','utf-8')
        text = instream.read()
        wlist = text.split()
        for e in wlist:
            count = self.all_dict.get(e,0)
            count +=1
            self.all_dict[e] = count


    def base_prob(self,word):
        """
        """
        l = len(word)
        p = 1.0/self.charsetsize
        return (0.5**l) *(p**l)*ALPHA
    
    def add(self,word):
        """
        """
        count = self.all_dict.get(word,0)
        count += 1
        self.all_dict[word] = count

    def subtract(self,word):
        """
        """
        count = self.all_dict[word] 
        count -= 1
        if(count ==0):
            del self.all_dict[word]
        if(count < 0):
            print 'seriour error!!'
        if(count > 0): 
            self.all_dict[word] = count
     
    def compute_seg_prob(self,left,right,joint):
        """
        """
        wordsize = len(self.all_dict)
        joint_count = self.all_dict.get(joint,0)
        left_count = self.all_dict.get(left,0)
        right_count = self.all_dict.get(right,0)
        factor0 = (self.base_prob(joint)+joint_count)
        factor1 = (self.base_prob(left)+left_count)*(self.base_prob(right)+right_count)*0.99
        ratio_1to0 = 1.0*factor1/((ALPHA+wordsize-2)*factor0)
        return ratio_1to0/(ratio_1to0+1)
    
    def gibbs_sample(self,T):
        """
        对隐变量进行循环采样
        """
        for i in range(T):
            if(i%100 == 0):
                print i
            if(i%30000 == 0):
                self.storeresult(i)
            
            for findex in range(self.corpsize-1):
                #print findex
                oldflag = self.flaglist[findex]
                right_seq = list()
                cur_index = findex
                left_seq = list() 
                cur_char = self.charlist[findex]
                for ri in range(cur_index-1,-2,-1):
                    if(ri==-1):
                        break
                    f = self.flaglist[ri]
                    if(f == 1):
                        break
                left_seq = self.charlist[ri+1:cur_index+1]

                for ci in range(cur_index+1,self.corpsize):
                    if(ci== self.corpsize-1):
                        right_seq.append(self.charlist[ci])
                        break
                    f = self.flaglist[ci]
                    right_seq.append(self.charlist[ci])
                    if(f==1):
                        break

                left_string = ''.join(left_seq)
                right_string = ''.join(right_seq)
                joint_word = ''.join(left_seq+right_seq)

                prob1 = 0
                #除去zi
                if(oldflag == 0):
                    self.subtract(joint_word)
                else:
                    self.subtract(left_string)
                    self.subtract(right_string)
                
                #计算采样概率
                prob1=  self.compute_seg_prob(left_string,right_string,joint_word)
                #进行采样
                newflag = self.bernuoli(prob1)
                #print 'f:'+str(flag)
                self.flaglist[findex] = newflag

                if(newflag ==0):
                    self.add(joint_word)
                else:
                    self.add(left_string)
                    self.add(right_string)
        self.storeresult(T)  

    def start(self):
        """
        """
        instream = sopen(self.cfile,'r','utf-8')
        for line in instream.readlines():
            nline = line.strip()
            ls = nline.split()
            for l in ls:
                for c in l:
                     self.charlist.append(c)
                     self.charset.add(c)
        self.corpsize = len(self.charlist)
        self.charsetsize = len(self.charset)

        for i in range(self.corpsize-1):
            x = self.bernuoli(0.5)
            self.flaglist.append(x)
        instream.close()
        self.storeresult(0)
        
    def bernuoli(self,p):
        """
        按照指定概率对结果采样,输出1的概率
        """
        f = random.random()
        if(f<p):
            return 1
        else:
            return 0
    
    def do_training(self):
        """
        """
        self.start()
        self.initcount()
        self.gibbs_sample(150000)
   
    def start_inference(self):
        """
        """
        flaglist = list()
        instream = sopen(self.cfile,'r','utf-8')
        for line in instream.readlines():
            text = line.strip()
            #获取flaglist 和charlist信息
            csize = len(text)
            lim = csize -1
            i=0
            while(i<csize):
                cele = text[i]
                self.charset.add(cele)
                self.charlist.append(cele)
                flag = cmp(cele,' ')
                if(flag == 0):
                   print 'wrong'
                if(i == lim):
                   self.flaglist.append(1)
                else:
                   nele = text[i+1]
                   flag = cmp(nele,' ')
                   if(flag == 0):
                       i += 1
                       self.flaglist.append(1)
                   else:
                       self.flaglist.append(0)
                i+=1
            #获取词 
            wlist = text.split()
            for e in wlist:
                count = self.all_dict.get(e,0)
                count +=1
                self.all_dict[e] = count
        self.corpsize = len(self.charlist)
        self.charsetsize = len(self.charset)
        print 'corpsize'+str(self.corpsize) 
        size = len(self.flaglist)
        print 'flagsize'+str(size-1)
        self.flaglist.pop(size-1)

    def do_inference(self):
        """
        """
        self.start_inference()
        self.gibbs_sample(30000)

if __name__=='__main__':
   #u = uwseg('/home/wengwei/peopledaily/199801part.txt')
   #u = uwseg('/home/wengwei/国内103.content')   
   u = uwseg('/home/wengwei/segimprovetest/国内187.seg')
   u.do_inference()


        
