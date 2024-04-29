from sklearn.preprocessing import MinMaxScaler

def normalize(data):
    return list(MinMaxScaler().fit_transform(data.reshape(-1,1)).reshape(-1))