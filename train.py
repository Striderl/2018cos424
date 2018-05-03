import pandas as pd
import numpy as np
import os
from sklearn.metrics import roc_auc_score
import datetime
from sklearn.model_selection import KFold


def train(train_df, test_df, Model, predictors, target='is_attributed', Model_params = None,
          FOLDS=3, record=False, submit=False, plot_feature_importance=False, **kwargs):

    if not os.path.exists('Error'):
            os.makedirs('Error')
    time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if record:
        train_recorder = open('Error/%s_%s_params.txt' %(Model.__name__, time), 'w')
        train_recorder.write(Model.__name__ + '\n')

    submit_pred = []
    kfold_errors = []
    kf = KFold(n_splits=FOLDS, shuffle=True, random_state=66)
    print("start %d folds train....." %(FOLDS))
    for i, (train_index, valid_index) in enumerate(kf.split(train_df)):
        X_train = train_df.iloc[train_index][predictors]
        y_train = train_df.iloc[train_index][target]

        X_valid = train_df.iloc[valid_index][predictors]
        y_valid = train_df.iloc[valid_index][target]

        print(X_train.shape, y_train.shape)
        print('training for fold %d.......'%(i))
        model = Model(model_params=Model_params)
        model.fit(X_train, y_train, **kwargs)
        train_auc = roc_auc_score(y_train, model.predict(X_train))
        print("fold train auc: ", str(train_auc))

        print('validating for fold %d......'%(i))
        valid_auc = roc_auc_score(y_valid, model.predict(X_valid))
        kfold_errors.append(valid_auc)
        print("fold validation auc: ", str(valid_auc))

        if record:
            train_recorder.write('\nFold %d\n' %i)
            train_recorder.write('Parameters: %s\n' %model.get_params())
            feature_importances = model.get_features_importances
            if feature_importances is not None:
                train_recorder.write('Feature importances:\n%s\n' %feature_importances)
            train_recorder.write('Train error: ' + str(train_auc) + '\n')
            train_recorder.write('Validation error: ' + str(valid_auc) + '\n')

        if submit:
            print("making prediction on test set.....")
            submit_pred.append(model.predict(test_df[predictors]))

        if plot_feature_importance:
            model.plot_features_importances()

        print("------------------------------------")

    avg_fold_auc = np.mean(kfold_errors)
    if record:
        train_recorder.write("\nAverage cross validation mean auc: %f\n" %avg_fold_auc)
        train_recorder.close()
    print("average cross validation mean auc %f\n\n" %avg_fold_auc)

    if submit:
        if not os.path.exists("Submission"):
            os.makedirs("Submission")
        sub = pd.DataFrame()
        sub['click_id'] = test_df['click_id'].astype('int')
        sub['is_attributed'] = np.mean(submit_pred, axis=0)
        sub.to_csv('Submission/sub_it%s.csv'%(time),index=False, float_format='%.9f')

    with open('Error/experiments.txt', 'a') as record:
        record.write('\n\nTime: %s\n' %time)
        record.write('model_params:%s\n' %model.get_params())
        record.write('local validtion mean auc: %f\n' %avg_fold_auc)
        record.write('leaderboard:____________________________________\n')

    return avg_fold_auc
