import pickle


def load_it(pkl_path="data/pkl_default.pkl"):
    with open(pkl_path, "rb") as f:
        loaded_df = pickle.load(f)
    print("DB Load from " + pkl_path)
    return loaded_df


def save_it(pkl_path="data/pkl_default.pkl", data={}):
    with open(pkl_path, "wb") as f:
        pickle.dump(data, f)
    print("DB Save to " + pkl_path)
