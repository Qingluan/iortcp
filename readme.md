# local reverse tool
> based select io version
> supported by python3/python2.7

## benchmark

i do not know , and no test . **BUT** 
I use IO SELECT to implement it

## Usag

- step1 [in **<i>reachable</i>** host]

```bash
~ python revserse.py  12345:12346  
# connection between 12345 and 12346
# "left" is listen port  like 12345
# "right" is reverse listen port like 12346
```

- step2 [in internal local net / **can not be reachable** from outer net]

```bash
~ python reverse.py 22 - outer.com:12346 
# connect outer's 12346 port
# ready to recv data from outer then pass to local's 22 port
```

> now outer.com can be reach local's 22 port by

```bash
~ ssh -p 12345 root@outer.com
```

### of course you can use chains to finish some interesting thing.




