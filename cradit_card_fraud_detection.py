


import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt
from scipy import stats
import tensorflow as tf
import seaborn as sns
from pylab import rcParams
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import  LogisticRegression
from sklearn.manifold import TSNE
from sklearn.metrics import classification_report, accuracy_score
from keras.models import Model, load_model
from keras.layers import Input, Dense
from keras.callbacks import ModelCheckpoint, TensorBoard
from keras import regularizers, Sequential
from sklearn.preprocessing import StandardScaler
# %matplotlib inline
sns.set(style="whitegrid",
        palette='muted', font_scale=1.5)
rcParams['figure.figsize']=14, 8
RANDOM_SEED= 42
LABELS = ["Normal", "Fraud"]

df = pd.read_csv("creditcard.csv")
df.head()

df.shape
df.isnull().values.any()

#Checking the number of records of each kind of transaction class (Fraud and Normal)
count_classes = pd.value_counts(df['Class'], sort=True)
count_classes.plot(kind = "bar", rot=0)
plt.title("Transaction class distribution")
plt.xticks(range(2), LABELS)
plt.xlabel("Class")
plt.ylabel("Frequency")

frauds = df[df.Class == 1]
normal = df[df.Class == 0]
frauds.shape

normal.shape

#check the amount of money involved in each kind of transaction
#Fraud transactions
frauds.Amount.describe()

#Normal transactions
normal.Amount.describe()

#Representation of Amount
f, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
f.suptitle("Amount per transaction by class")
bins=50
ax1.hist(frauds.Amount, bins=bins)
ax1.set_title("Fraud")

ax2.hist(normal.Amount, bins = bins)
ax2.set_title("Normal")

plt.xlabel("Amount($)")
plt.ylabel("Number of Transactions")
plt.xlim((0, 200000))
plt.yscale('log')
plt.show()

#Plotting the time of transaction to check the correlation
f, (ax1,ax2) = plt.subplots(2, 1,sharex=True)
f.suptitle('Time of transaction vs Amount by class')

ax1.scatter(frauds.Time, frauds.Amount)
ax1.set_title("Fraud")

ax2.scatter(normal.Time, normal.Amount)
ax2.set_title("Normal")

plt.xlabel("Time (in Second)")
plt.ylabel("Amount")
plt.show()

data = df.drop(['Time'], axis=1)

#Scalling The Amount using StandardScaler
data['Amount'] = StandardScaler().fit_transform(data['Amount'].values.reshape(-1, 1))

#Building the Model
non_fraud = data[data['Class'] == 0]
fraud = data[data['Class'] == 1]

# Concatenate non-fraud and fraud dataframes
df = pd.concat([non_fraud, fraud]).sample(frac=1).reset_index(drop=True)

X = df.drop(['Class'], axis=1).values
Y = df['Class'].values

#Split the data into 80% Train and 20% testing
x_train, x_test = train_test_split(data, test_size=0.2, random_state=RANDOM_SEED)
x_train_fraud = x_train[x_train.Class == 1]
x_train = x_train[x_train.Class == 0]
x_train = x_train.drop(['Class'], axis=1)
y_test = x_test['Class']
x_test = x_test.drop(['Class'], axis=1)
x_train = x_train.values
x_train.shape

#AutoEncoder Model
input_layer = Input(shape=(X.shape[1],))
# encoding part
encoded = Dense(100, activation= 'tanh', activity_regularizer=regularizers.l1(10e-5))(input_layer)
encoded = Dense(50,activation='relu')(encoded)

#Decoding part
decoded=Dense(50,activation="tanh")(encoded)
decoded = Dense(100, activation="tanh")(decoded)

 #output layer
output_layer = Dense(X.shape[1], activation="relu")(decoded)

#Training the model
autoencoder = Model(input_layer, output_layer)
autoencoder.compile(optimizer="adadelta", loss="mse")

#Scalling the values
X= data.drop(["Class"], axis=1)
Y = data["Class"].values

x_scale = MinMaxScaler().fit_transform(X.values)
x_norm, x_fraud = x_scale[Y ==0], x_scale[Y==1]

autoencoder.fit(x_norm[0:2000],x_norm[0:2000],
                batch_size= 256, epochs=10,
                shuffle=True, validation_split = 0.20
                )

#The Hidden Representation
hidden_representation = Sequential()
hidden_representation.add(autoencoder.layers[0])
hidden_representation.add(autoencoder.layers[1])
hidden_representation.add(autoencoder.layers[2])

#Model Prediction
norm_hid_rep = hidden_representation.predict(x_norm[:3000])
fraud_hid_rep = hidden_representation.predict(x_fraud)

#Getting the representation Data
rep_x= np.append(norm_hid_rep, fraud_hid_rep, axis=0)
y_n = np.zeros(norm_hid_rep.shape[0])
y_f = np.ones(fraud_hid_rep.shape[0])
rep_y = np.append(y_n, y_f)

#Train,Test
train_x, val_x, train_y,val_y = train_test_split(rep_x, rep_y, test_size=0.25)

clf = LogisticRegression(solver="lbfgs").fit(train_x, train_y)
pred_y = clf.predict(val_x)

print("Classification Report: ")
print(classification_report(val_y, pred_y))

print("")
print("Accuracy Score: ",accuracy_score)

