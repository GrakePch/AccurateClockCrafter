from PIL import Image

def inv_interp(lower, upper, value):
    return (value - lower) / (upper - lower)

def interp(lower, upper, value):
    return (1 - value) * lower + value * upper

def mask_subtract(i1, i2):
    alpha1 = list(i1.split()[-1].getdata())
    alpha2 = list(i2.split()[-1].getdata())
    
    result_alpha = []
    for p1, p2 in zip(alpha1, alpha2):
        p_new = max(p1 - p2, 0)
        result_alpha.append(p_new)
        
    result_mask = Image.new("L", i1.size)
    result_mask.putdata(result_alpha)
    return result_mask