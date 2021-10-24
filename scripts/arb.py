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
mobi_swap_addr = "0x413FfCc28e6cDDE7e93625Ef4742810fE9738578"


EDGE = 70
PRICE = (10000 + EDGE) / 10000
SLIPPAGE = .0005
START = 300


def get_amount_out(amount_in, reserve_in, reserve_out):
    amount_in_with_fee = amount_in * 997
    numerator = amount_in_with_fee * reserve_out
    denominator = reserve_in * 1000 + amount_in_with_fee
    return numerator / denominator


def ube_swap(amount_in, amount_out, path, account, router):
    router.swapExactTokensForTokens(amount_in, amount_out*(1-SLIPPAGE), 
        path, account, int(time.time())+30, {"from": account})
    print('ube')


def mobi_swap(amount_in, amount_out, from_index, to_index, account, swap):
    swap.swap(from_index, to_index, amount_in, amount_out*(1-SLIPPAGE),
        int(time.time())+30, {"from": account})
    print('mobi')


def check_ube(price, prev_balance, path, account, router):
    if price > PRICE:
        # Find optimal trade
        marginal_return = price
        amount = 10 ** 18
        total_return = marginal_return
        while True:
            marginal_return = (router.getAmountsOut(amount + 10**18, path)[-1] / 10**18) - total_return
            if (marginal_return > 1):
                if (amount > prev_balance): break
                amount += 10 ** 18
                total_return += marginal_return
            else:
                break  

        #make the trade
        amount = min(amount, prev_balance)
        if (amount > 0):
            ube_swap(amount, total_return, path, account, router)


def check_mobi(price, prev_balance, from_index, to_index, account, swap):
    if price > PRICE:
        # celo to pcelo
        marginal_return = price
        amount = 10 ** 18
        total_return = marginal_return
        while True:
            marginal_return = (swap.calculateSwap(from_index, to_index, amount + 10**18) / 10**18) - total_return
            if (marginal_return > 1):
                if (amount > prev_balance): break
                amount += 10 ** 18
                total_return += marginal_return
            else:
                break  

        #make the trade
        amount = min(amount, prev_balance)
        if (amount > 0):
            mobi_swap(amount, total_return, from_index, to_index, account, swap)


def main():
    network.gas_limit(8000000)
    account = accounts.load('bot')
    celo = interface.ERC20(celo_addr)
    pcelo = interface.ERC20(pcelo_addr)

    router = UniswapV2Router02.at(router_addr)
    swap = interface.ISwap(mobi_swap_addr)

    path = [celo_addr, ube_addr, poof_addr, pcelo_addr]

    swap_map = {}

    for coin in [celo, pcelo]:
        index = swap.getTokenIndex(coin)
        swap_map.update({coin.address: index})
        # coin.approve(swap, 2**256-1, {"from": account})
        # coin.approve(router, 2**256-1, {"from": account})
 
    while True:
        prevCelo = celo.balanceOf(account)
        prevPCelo = pcelo.balanceOf(account)

        poofPerGdl = router.getAmountsOut(10**18, [celo_addr, ube_addr, poof_addr, pcelo_addr])[-1] / 10**18
        gldPerPoof = router.getAmountsOut(10**18, [pcelo_addr, poof_addr, ube_addr, celo_addr])[-1] / 10**18

        mob01 = swap.calculateSwap(0, 1, 10**18) / 10 ** 18
        mob10 = swap.calculateSwap(1, 0, 10 ** 18) / 10 ** 18 

        print('poofPerGLD', poofPerGdl)
        print('gldPerPoof', gldPerPoof)
        print('mob01', mob01)
        print('mob10', mob10)
        print()

        check_ube(poofPerGdl, prevCelo, path, account, router)
        check_ube(gldPerPoof, prevPCelo, path[::-1], account, router)
        prevCelo = celo.balanceOf(account)
        prevPCelo = pcelo.balanceOf(account)
        check_mobi(poofPerGdl, prevCelo, 0, 1, account, swap)
        check_mobi(gldPerPoof, prevPCelo, 1, 0, account, swap)

        if poofPerGdl > PRICE or gldPerPoof > PRICE or mob01 > PRICE or mob10 > PRICE:
            print('mobi')
            print("celo", celo.balanceOf(account) / 10 ** 18)
            print("pcelo", pcelo.balanceOf(account) / 10 ** 18)
            print("gain", (celo.balanceOf(account) + pcelo.balanceOf(account) - prevCelo - prevPCelo) / 10 ** 18)
            print()
        time.sleep(4)