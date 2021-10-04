import json


def init_db():
    data_A = {'A': 100}
    data_B = {'B': 100}
    data_C = {'C': 100}
    with open('data_A.json', 'w') as fp:
        json.dump(data_A, fp)
    with open('data_B.json', 'w') as fp:
        json.dump(data_B, fp)
    with open('data_C.json', 'w') as fp:
        json.dump(data_C, fp)


def execute_op(job_to_exec):
    """
    execute the job in self.job_to_exec
    """
    [action, user, amount] = job_to_exec
    with open('data_{}.json'.format(user), 'r') as fp:
        data = json.load(fp)
    if action == 'DepositCash':
        old_ = data[user]
        data[user] = data[user] + amount
        print("DepositCash to User {}, amount:{}->{} ".format(user, old_, data[user]))
    elif action == 'WithdrawCash':
        old_ = data[user]
        data[user] = data[user] - amount
        print("WithdrawCash to User {}, amount:{}->{} ".format(user, old_, data[user]))
    elif action == 'ApplyInterest':
        old_ = data[user]
        data[user] = data[user] * (1 + amount)
        print("ApplyInterest to User {}, amount:{}->{} ".format(user, old_, data[user]))
    elif action == 'CheckBalance':
        print("CheckBalance to User {}, amount:{}".format(user, data[user]))
    else:
        assert False
    with open('data_{}.json'.format(user), 'w') as fp:
        json.dump(data, fp)


if __name__ == '__main__':
    init_db()
