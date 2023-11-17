def calc(k):
    print('\nl1\n')
    for a in range(1, k ** 1 + 1):
        print(f'A{a}')
    print('\nl2\n')
    for e in range(1, k ** 2 + 1):
        print(f'A{(e + k - 1) // k}  E{e}')
    print('\nl3\n')
    for h in range(1, k**3 + 1):
        print(f'A{(h + k ** 2 - 1) // (k ** 2)}  E{(h + k - 1) // k}  H{h}')

def calc2(k):
    edge_c = 1
    host_c = 1
    print('\nl1\n')
    for a in range(k):
        print(f'A{a}')
        for e in range(k):
            print(f'A{a}  E{edge_c}')
            edge_c += 1
            for h in range(k):
                print(f'A{a}  E{edge_c}  H{h}')
calc2(2)