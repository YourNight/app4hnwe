import random


def case_code(file_path):
    print(file_path)
    return 'No.'+str(random.randint(0, 1000000))

def bottle_codes(file_path):
    rst = {}
    rst[0] = str(6666)
    # rst[0] = str(random.randint(0, 1000000))
    rst[1] = str(random.randint(0, 1000000))
    rst[2] = str(random.randint(0, 1000000))
    return rst

def bottle_code(file_path):
    return str(random.randint(0, 1000000))
