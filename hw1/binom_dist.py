from scipy.stats import binom

def binomial_distribution():
    n = 50
    p = 0.2
    k = 10
    return binom.sf(k, n, p)

if __name__ == "__main__":
    print(binomial_distribution())