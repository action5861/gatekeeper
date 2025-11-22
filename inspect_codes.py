for code in [0xD130, 0xD134, 0xD140, 0xD138]:
    ch = chr(code)
    print(hex(code), ch.encode('unicode_escape'))
