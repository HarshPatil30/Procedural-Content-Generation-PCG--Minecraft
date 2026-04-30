import torch
p='output/try2_examples/torch_blockdata/0.pt'
obj=torch.load(p)
print('type:',type(obj))
try:
    if isinstance(obj, tuple):
        print('tuple len',len(obj))
        for i,el in enumerate(obj[:3]):
            print('el',i,type(el), getattr(el,'shape',None))
    else:
        print('obj',obj, getattr(obj,'shape',None))
except Exception as e:
    print('err',e)
