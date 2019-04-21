# -*- coding: utf-8 -*-
"""
Created on Tue Jun 26 14:48:05 2018

@author: xal
"""

from keras.models import Sequential
from keras.layers.normalization import BatchNormalization
from sklearn.metrics import roc_curve, auc, roc_auc_score,average_precision_score
import numpy as np
from keras.layers.core import Dense, Dropout, Merge
import utils.tools as utils
from keras.regularizers import l2
from gensim.models.word2vec import Word2Vec
import copy
import h5py
from sklearn.model_selection import StratifiedKFold
from keras.models import load_model
import random
from sklearn.preprocessing import StandardScaler
from gensim.models import Word2Vec
from keras.optimizers import SGD




def read_NO(file_name):
#    # read sample from a file
    no = []
    with open(file_name, 'r') as fp:
        i = 0
        for line in fp:
            if i%2==0:
                no.append(int(line.strip().split(':')[1].split('N|')[0]))
            i = i+1       
    return   no  
    
def read_file(file_name):
    # read sample from a file
    seq = []
    with open(file_name, 'r') as fp:
        i = 0
        for line in fp:
            if i%2==0:
                seq.append(line.split('\n')[0])
            i = i+1       
    return   seq   
    
def get_index2seq_dict():
    file_name = 'dataset/11188/protein'
    seq = []
    index = []
    
    with open(file_name, 'r') as fp:
        
        i = 0
        for line in fp:
            if i%2==0:
                index.append(int(line.strip().split(':')[1].split('N|')[0]))
            if i%2==1:
                seq.append(line.split('\n')[0])
            i = i+1    
    
    dict_index2seq = dict()
    for i in range(len(index)):
        dict_index2seq[index[i]] = seq[i]

    return dict_index2seq
    
def pandding_J(protein,maxlen):           
    padded_protein = copy.deepcopy(protein)   
    for i in range(len(padded_protein)):
        if len(padded_protein[i])<maxlen:
            for j in range(len(padded_protein[i]),maxlen):
                padded_protein[i].append('J')
    return padded_protein  
    

def protein_representation(wv,tokened_seq_protein,maxlen,size):  
    represented_protein  = []
    for i in range(len(tokened_seq_protein)):
        temp_sentence = []
        for j in range(maxlen):
            if tokened_seq_protein[i][j]=='J':
                temp_sentence.extend(np.zeros(size))
            else:
                temp_sentence.extend(wv[tokened_seq_protein[i][j]])
        represented_protein.append(np.array(temp_sentence))    
    return represented_protein
       

    
def token(dataset):
    token_dataset = []
    for i in range(len(dataset)):
        seq = []
        for j in range(len(dataset[i])):
            seq.append(dataset[i][j])
        token_dataset.append(seq)  
        
    return  token_dataset

def connect(protein_A,protein_B):
    # contect protein A and B
    protein_AB = []
    for i in range(len(protein_A)):
        con = protein_A[i] + protein_B[i] 
        protein_AB.append(con)
        
    return np.array(protein_AB)
   
      
def split_train_c1_c2_c3_dataset():

    file_1 = 'dataset/11188/positive/Protein_A.txt'
    file_2 = 'dataset/11188/positive/Protein_B.txt'
    file_3 = 'dataset/11188/negative/Protein_A.txt'
    file_4 = 'dataset/11188/negative/Protein_B.txt'
    #  index for protein 
    pos_NO_A = read_NO(file_1)
    pos_NO_B = read_NO(file_2)
    neg_NO_A = read_NO(file_3)
    neg_NO_B = read_NO(file_4)
    
    # all pairs
    pairs = []
    for i in range(len(pos_NO_A)):
        pairs.append([pos_NO_A[i],pos_NO_B[i],1])
    for i in range(len(neg_NO_A)):
        pairs.append([neg_NO_A[i],neg_NO_B[i],0])
    pairs = np.array(pairs)   
    
    # all proteins
    all_no = copy.deepcopy(pos_NO_A)
    all_no.extend(pos_NO_B)
    all_no.extend(neg_NO_A)
    all_no.extend(neg_NO_B)
    
    list_all_no = list(set(all_no))
    np_all_no = np.array(list_all_no)
   
    
    # shuffle
    random.seed(20181110)
    index = [i for i in range(len(np_all_no))]
    random.shuffle(index) 
    shuffled_np_all_no = np_all_no[index]
    # 50 for c3,2000 for c1
    no530 =  shuffled_np_all_no[:300]
    no2000 = shuffled_np_all_no[300:]

    # train and c1
    k=0
    train_c1 = []

    for i in range(len(pairs)):
        if pairs[i,0] in no2000 and pairs[i,1] in no2000:
            train_c1.append(pairs[i])
            k=k+1
            print('i:',i,'  k:',k)
            
   
    # train and c1
    np_train_c1 = np.array(train_c1)
    random.seed(20181110)
    index_train_c1 = [i for i in range(len(np_train_c1))]
    random.shuffle(index_train_c1) 
    shuffled_np_train_c1 = np_train_c1[index_train_c1]

    # 1/5 for c1,4/5 for train
    c1 =  shuffled_np_train_c1[:int(float(1)/5*len(np_train_c1))]
    train = shuffled_np_train_c1[int(float(1)/5*len(np_train_c1)):]

    # c3          
    m=0
    c3=[]
    for i in range(len(pairs)):
        if pairs[i,0] in no530 and pairs[i,1] in no530:
            c3.append(pairs[i])
            m=m+1
            print('i:',i,'  m:',m)
            
           
    c3 = np.array(c3)               
    
    # c2         
    n = 0
    c2 = []
    for i in range(len(pairs)):
        if (pairs[i,0] in no530 and pairs[i,1] in no2000) or (pairs[i,0] in no2000 and pairs[i,1] in no530):
            c2.append(pairs[i])
            n=n+1
            print('i:',i,'  n:',n)
            
                        
    c2 = np.array(c2)               
    
    return train,c1,c2,c3
    
    
def get_each_dataset(dict_index2seq, wv, dataset_index_pairs,maxlen,size):
    
    seq_dataset = []
    for i in range(len(dataset_index_pairs)):
        seq_dataset.append([dict_index2seq[dataset_index_pairs[i][0]],dict_index2seq[dataset_index_pairs[i][1]]])
    seq_dataset = np.array(seq_dataset)
    # token
    token_seq_protein_A = token(seq_dataset[:,0])
    token_seq_protein_B = token(seq_dataset[:,1])
    
    # padding
    tokened_token_seq_protein_A = pandding_J(token_seq_protein_A,maxlen)
    tokened_token_seq_protein_B = pandding_J(token_seq_protein_B,maxlen)

    # protein reprsentation
    feature_protein_A  = protein_representation(wv,tokened_token_seq_protein_A,maxlen,size)
    feature_protein_B  = protein_representation(wv,tokened_token_seq_protein_B,maxlen,size)
    # put two part together
    feature_protein_AB = np.hstack((np.array(feature_protein_A),np.array(feature_protein_B)))
          
    return np.array(feature_protein_AB)
    
    

def merged_DBN(sequence_len):
    # left
    model_left = Sequential()
    model_left.add(Dense(2048, input_dim=sequence_len ,activation='relu',W_regularizer=l2(0.01)))
    model_left.add(BatchNormalization())
    model_left.add(Dropout(0.5))
    model_left.add(Dense(1024, activation='relu',W_regularizer=l2(0.01)))
    model_left.add(BatchNormalization())
    model_left.add(Dropout(0.5))
    model_left.add(Dense(512, activation='relu',W_regularizer=l2(0.01)))
    model_left.add(BatchNormalization())
    model_left.add(Dropout(0.5))
    model_left.add(Dense(128, activation='relu',W_regularizer=l2(0.01)))
    model_left.add(BatchNormalization())
    
    
    # right
    model_right = Sequential()
    model_right.add(Dense(2048,input_dim=sequence_len,activation='relu',W_regularizer=l2(0.01)))
    model_right.add(BatchNormalization())
    model_right.add(Dropout(0.5))   
    model_right.add(Dense(1024, activation='relu',W_regularizer=l2(0.01)))
    model_right.add(BatchNormalization())
    model_right.add(Dropout(0.5))
    model_right.add(Dense(512, activation='relu',W_regularizer=l2(0.01)))
    model_right.add(BatchNormalization())
    model_right.add(Dropout(0.5))
    model_right.add(Dense(128, activation='relu',W_regularizer=l2(0.01)))
    model_right.add(BatchNormalization())
    # combine
    merged = Merge([model_left, model_right])
   
    model = Sequential()
    model.add(merged)
    model.add(Dense(8, activation='relu',W_regularizer=l2(0.01)))
    model.add(BatchNormalization())
    model.add(Dropout(0.5))
    model.add(Dense(2, activation='softmax'))
   
    
    return model

def print_result(predictions_test,y_test):
    auc_test = roc_auc_score(y_test[:,1], predictions_test[:,1])
    pr_test = average_precision_score(y_test[:,1], predictions_test[:,1])
 
    label_predict_test = utils.categorical_probas_to_classes(predictions_test)  
    tp_test,fp_test,tn_test,fn_test,accuracy_test, precision_test, sensitivity_test,recall_test, specificity_test, MCC_test, f1_score_test,_,_,_= utils.calculate_performace(len(label_predict_test), label_predict_test, y_test[:,1])
    print('\ttp=%0.0f,fp=%0.0f,tn=%0.0f,fn=%0.0f'%(tp_test,fp_test,tn_test,fn_test))
    print('\tacc=%0.4f,pre=%0.4f,rec=%0.4f,sp=%0.4f,mcc=%0.4f,f1=%0.4f'
          % (accuracy_test, precision_test, recall_test, specificity_test, MCC_test, f1_score_test))
    print('\tauc=%0.4f,pr=%0.4f'%(auc_test,pr_test))
    print('========================')
    
def save_data(train_fea_protein_AB, c2_fea_protein_AB,c3_fea_protein_AB, c1_fea_protein_AB):
    #scaler
    scaler = StandardScaler().fit(train_fea_protein_AB)
    scalered_train_fea_protein_AB = scaler.transform(train_fea_protein_AB)   
    
    # creat HDF5 file
    h5_file = h5py.File('dataset/c1c2c3/special_cv_11188.h5','w')
    
    h5_file.create_dataset('trainset_x', data = scalered_train_fea_protein_AB)
    h5_file.create_dataset('trainset_y', data = train[:,-1])
    # get c1 data  ==========================================================================
   
    #scaler
    scalered_c1_fea_protein_AB = scaler.transform(c1_fea_protein_AB)   
       
    h5_file.create_dataset('c1_x', data = scalered_c1_fea_protein_AB)
    h5_file.create_dataset('c1_y', data = c1[:,-1])
        
    # get c2 data  ==========================================================================
    
    #scaler
    scalered_c2_fea_protein_AB = scaler.transform(c2_fea_protein_AB)   
       
    h5_file.create_dataset('c2_x', data = scalered_c2_fea_protein_AB)
    h5_file.create_dataset('c2_y', data = c2[:,-1])
    
    # get c3 data  ==========================================================================
   
    #scaler
    scalered_c3_fea_protein_AB = scaler.transform(c3_fea_protein_AB)   
       
    h5_file.create_dataset('c3_x', data = scalered_c3_fea_protein_AB)
    h5_file.create_dataset('c3_y', data = c3[:,-1])
    h5_file.close()
    
    return scalered_train_fea_protein_AB,scalered_c1_fea_protein_AB,scalered_c2_fea_protein_AB,scalered_c3_fea_protein_AB
             
        
#%%    
if __name__ == "__main__":    
    maxlen = 550
    size = 20
    sequence_len = maxlen*size
    # word2vec
    dict_index2seq = get_index2seq_dict()
    
    # data
    train,c1,c2,c3 = split_train_c1_c2_c3_dataset()
    
    # load Word2Vec MODEL
    model_wv = Word2Vec.load('model/word2vec/wv_swissProt_size_20_window_4.model')
    
       
    # get training data =====================================================================
    train_fea_protein_AB = get_each_dataset(dict_index2seq, model_wv.wv, train[:,0:-1],maxlen,size)
    print('train_fea_protein_AB')
    c1_fea_protein_AB = get_each_dataset(dict_index2seq, model_wv.wv, c1[:,0:-1],maxlen,size)
    print('c1_fea_protein_AB')
    c2_fea_protein_AB = get_each_dataset(dict_index2seq, model_wv.wv, c2[:,0:-1],maxlen,size)
    print('c2_fea_protein_AB')
    c3_fea_protein_AB = get_each_dataset(dict_index2seq, model_wv.wv, c3[:,0:-1],maxlen,size)
    print('c3_fea_protein_AB')
    
    scalered_train_fea_protein_AB,scalered_c1_fea_protein_AB,scalered_c2_fea_protein_AB,scalered_c3_fea_protein_AB = save_data(train_fea_protein_AB, c2_fea_protein_AB,c3_fea_protein_AB, c1_fea_protein_AB)
    
    # train data and label
    X_train_left = np.array(scalered_train_fea_protein_AB[:,0:sequence_len])
    X_train_right = np.array(scalered_train_fea_protein_AB[:,sequence_len:sequence_len*2])
         
    Y_train = utils.to_categorical(train[:,-1]) 
       
    # c1 
    c1_test_left = np.array(scalered_c1_fea_protein_AB[:,0:sequence_len])
    c1_test_right = np.array(scalered_c1_fea_protein_AB[:,sequence_len:sequence_len*2])
         
    Y_c1 = utils.to_categorical(c1[:,-1]) 
       
    # c2 
    c2_test_left = np.array(scalered_c2_fea_protein_AB[:,0:sequence_len])
    c2_test_right = np.array(scalered_c2_fea_protein_AB[:,sequence_len:sequence_len*2])
         
    Y_c2 = utils.to_categorical(c2[:,-1]) 
     
    # c3 
    c3_test_left = np.array(scalered_c3_fea_protein_AB[:,0:sequence_len])
    c3_test_right = np.array(scalered_c3_fea_protein_AB[:,sequence_len:sequence_len*2])
         
    Y_c3 = utils.to_categorical(c3[:,-1]) 
    '''
    # feed data into model
    # compile model
    model =  merged_DBN(sequence_len)   
    sgd = SGD(lr=0.01, momentum=0.9, decay=0.001)
    model.compile(loss='categorical_crossentropy', optimizer=sgd,metrics=['accuracy'])
  
    model.fit([X_train_left, X_train_right], Y_train,
              batch_size = 128,
              nb_epoch = 35,
              verbose = 1)  
    
    print('******   model created!  ******')
    model.save('model/c1c2c3/model.h5')
    '''
    model = load_model('model/c1c2c3/model.h5')
    # predict c1
    predictions_test_c1 = model.predict([c1_test_left, c1_test_right]) 
    print_result(predictions_test_c1,Y_c1)
    # predict c2
    predictions_test_c2 = model.predict([c2_test_left, c2_test_right]) 
    print_result(predictions_test_c2,Y_c2)
    # predict c3
    predictions_test_c3 = model.predict([c3_test_left, c3_test_right]) 
    print_result(predictions_test_c3,Y_c3)
   
        
    
        
    