class Dispensor:
    
    def __init__(self, data, batch_size):
        self.data = data
        self.size = len(data)
        self.batch_size = batch_size
    def __iter__(self):
        self.idx = 0
        return self

    def __next__(self):
        if self.idx*self.batch_size >= self.size:
            raise StopIteration

        temp = self.data[self.idx * self.batch_size : (self.idx+1)* self.batch_size]

        self.idx += 1
        return temp

li = [i for i in range(360)]
d = Dispensor(li, 14)
for i,v in enumerate(d):
    print(i, v)