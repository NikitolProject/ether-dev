def test(*args, **kwargs):
    print(type(args))
    print(type(kwargs))
    print(args)
    print(kwargs)

test("sadsd", "asd", t=1, tt=2)
