from brownie import (
    interface,
    accounts,
    UniswapV2Router02,
    network,
)
import time


celo_addr = "0x471EcE3750Da237f93B8E339c536989b8978a438"
ube_addr = "0x00Be915B9dCf56a3CBE739D9B9c202ca692409EC"
poof_addr = "0x00400FcbF0816bebB94654259de7273f4A05c762"
pcelo_addr = "0xE74AbF23E1Fdf7ACbec2F3a30a772eF77f1601E1"
factory_addr = "0x62d5b84bE28a183aBB507E125B384122D2C25fAE"
router_addr = "0xE3D8bd6Aed4F159bc8000a9cD47CffDb95F96121"


EDGE = 5
PRICE = (10000 + EDGE) / 10000
SLIPPAGE = .0005
START = 300

def get_amount_out(amount_in, reserve_in, reserve_out):
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    return numerator / denominator

def main():
    network.gas_limit(8000000)
    account = accounts.load('bot')
    celo = interface.ERC20(celo_addr)
    pcelo = interface.ERC20(pcelo_addr)

    router = UniswapV2Router02.at(router_addr)
    swap = interface.ISwap("0x413FfCc28e6cDDE7e93625Ef4742810fE9738578")

    swap_map = {}

    for coin in [celo, pcelo]:
        index = swap.getTokenIndex(coin)
        swap_map.update({coin.address: index})
        # coin.approve(swap, 2**256-1, {"from": account})
        # coin.approve(router, 2**256-1, {"from": account})
 
    print(swap_map)

    while True:
        prevCelo = celo.balanceOf(account)
        prevPCelo = pcelo.balanceOf(account)

        poofPerGdl = router.getAmountsOut(10**18, [celo_addr, ube_addr, poof_addr, pcelo_addr])[-1] / 10**18
        gldPerPoof = router.getAmountsOut(10**18, [pcelo_addr, poof_addr, ube_addr, celo_addr])[-1] / 10**18

        mob01 = swap.calculateSwap(0, 1, 10**18) / 10 ** 18
        mob10 = swap.calculateSwap(1, 0, 10 ** 18) / 10 ** 18 

        # print('poofPerGLD', poofPerGdl)
        # print('gldPerPoof', gldPerPoof)
        # print('mob01', mob01)
        # print('mob10', mob10)

        if poofPerGdl > PRICE:
            # CELO to PCELO
            #find optimal trade
            marginal_return = poofPerGdl
            amount = 10 ** 18
            total_return = marginal_return
            while True:
                marginal_return = (router.getAmountsOut(amount + 10**18, [celo_addr, ube_addr, poof_addr, pcelo_addr])[-1] / 10**18) - total_return
                if (marginal_return > PRICE):
                    if (amount > prevCelo): break
                    amount += 10 ** 18
                    total_return += marginal_return
                else:
                    break  

            #make the trade
            amount = min(amount, prevPCelo)
            if (amount > 0):
                router.swapExactTokensForTokens(amount, total_return*(1-SLIPPAGE), 
                    [celo_addr, ube_addr, poof_addr, pcelo_addr], account, int(time.time())+30, {"from": account})
                    
        elif gldPerPoof > PRICE:
            # PCELO to CELO
            #find optimal trade
            marginal_return = gldPerPoof
            amount = 10 ** 18
            total_return = marginal_return
            while True:
                marginal_return = (router.getAmountsOut(amount + 10**18, [pcelo_addr, poof_addr, ube_addr, celo_addr])[-1] / 10**18) - total_return
                if (marginal_return > PRICE):
                    if (amount > prevPCelo): break
                    amount += 10 ** 18
                    total_return += marginal_return
                else:
                    break  

            #make the trade
            amount = min(amount, prevPCelo)
            if (amount > 0):
                router.swapExactTokensForTokens(amount, total_return*(1-SLIPPAGE), 
                    [pcelo_addr, poof_addr, ube_addr, celo_addr], account, int(time.time())+30, {"from": account})

        if poofPerGdl > PRICE or gldPerPoof > PRICE:
            print('ube')
            print("celo", celo.balanceOf(account) / 10 ** 18)
            print("pcelo", pcelo.balanceOf(account) / 10 ** 18)
            print("gain", (celo.balanceOf(account) + pcelo.balanceOf(account) - prevCelo - prevPCelo) / 10 ** 18)
            print()

        prevCelo = celo.balanceOf(account)
        prevPCelo = pcelo.balanceOf(account)

        if mob01 > PRICE:
            # celo to pcelo
            marginal_return = mob01
            amount = 10 ** 18
            total_return = marginal_return
            while True:
                marginal_return = (swap.calculateSwap(0, 1, amount + 10**18) / 10**18) - total_return
                if (marginal_return > PRICE):
                    if (amount > prevCelo): break
                    amount += 10 ** 18
                    total_return += marginal_return
                else:
                    break  

            #make the trade
            if (prevPCelo > (START * 10 ** 18)): 
                amount = min(amount, prevPCelo - (START * 10 ** 18))
                if (amount > 0):
                    swap.swap(0, 1, amount, total_return*(1-SLIPPAGE), int(time.time())+30, {"from": account})

        elif mob10 > PRICE:
            # pcelo to celo
            #find optimal trade
            marginal_return = mob10
            amount = 10 ** 18
            total_return = marginal_return
            while True:
                marginal_return = (swap.calculateSwap(1, 0, amount + 10**18) / 10**18) - total_return
                if (marginal_return > PRICE):
                    if (amount > prevPCelo): break
                    amount += 10 ** 18
                    total_return += marginal_return
                else:
                    break  

            #make the trade
            amount = min(amount, prevPCelo)
            if (amount > 0):
                swap.swap(1, 0, amount, total_return*(1-SLIPPAGE), int(time.time())+30, {"from": account})


        if mob01 > PRICE or mob10 > PRICE:
            print('mobi')
            print("celo", celo.balanceOf(account) / 10 ** 18)
            print("pcelo", pcelo.balanceOf(account) / 10 ** 18)
            print("gain", (celo.balanceOf(account) + pcelo.balanceOf(account) - prevCelo - prevPCelo) / 10 ** 18)
            print()
        time.sleep(4)