import asyncio
import json
import base58
import base64
from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.message import MessageV0, MessageHeader
from solders.instruction import AccountMeta, CompiledInstruction, Instruction
from jito_py_rpc import JitoJsonRpcSDK
from solders.transaction import VersionedTransaction
from solders.message import MessageV0
from solders.hash import Hash
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT as SYSVAR_RENT_PUBKEY
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from solders.instruction import Instruction as TransactionInstruction
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solana.rpc.commitment import Confirmed
from struct import pack
from solders.instruction import AccountMeta
import requests, os
from metadatafun import metadaturi  
import os
from struct import pack, unpack
from wall1buytext import create_buy_transaction
from wall2buytext import create_buy_transaction2
from wall3buytext import create_buy_transaction3
import sys


PUMP_FUN_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
FEE_RECIPIENT = Pubkey.from_string("62qc2CNXwrYqQScmEdiZFFAnJR262PxWEuNQtxfafNgV")
EVENT_AUTHORITY = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
METAPLEX_PROGRAM = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
client = Client("https://mainnet.helius-rpc.com/?api-key=bad4333f-cf37-4521-8a24-6a182bb0e579")

def load_key(label, filename="allkeys.txt"):
    with open(filename, "r") as f:
        for line in f:
            if line.strip().startswith(label):
                key = line.split("=")[1].strip().strip('"')
                return key
    raise ValueError(f"Label '{label}' not found in {filename}")

# get keys for jito tip and creator
base58_private_key = load_key("creator_wallet")
decoded = base58.b58decode(base58_private_key)
payer = Keypair.from_bytes(bytes(decoded))   
base58_private_key_jito_tip_account = load_key("walletforjitotip")
decoded_jito_tip_account = base58.b58decode(base58_private_key_jito_tip_account)
jito_tip_keypair = Keypair.from_bytes(bytes(decoded_jito_tip_account))
sender = jito_tip_keypair.pubkey()


mint = Keypair.from_bytes(base58.b58decode(open("pumpsuffix.txt").read().strip()))

tokenca = mint.pubkey()
lines = [
    " THIS BELOW IS TOKEN CONTRACT ADDRESS ",
    f" {tokenca} ",
]
width = max(len(line) for line in lines)
border = "+" + "-" * (width + 2) + "+"
print(border)
for line in lines:
    print(f"| {line.ljust(width)} |")
print(border)


global_pda, _ = Pubkey.find_program_address([b"global"], PUMP_FUN_PROGRAM)
bonding_curve_pda, _ = Pubkey.find_program_address(
    [b"bonding-curve", bytes(mint.pubkey())],
    PUMP_FUN_PROGRAM,
)
mint_auth_pda, _ = Pubkey.find_program_address([b"mint-authority"], PUMP_FUN_PROGRAM)
assoc_bonding = get_associated_token_address(bonding_curve_pda, mint.pubkey())
assoc_user = get_associated_token_address(payer.pubkey(), mint.pubkey())
metadata_pda, _ = Pubkey.find_program_address(
    [b"metadata", bytes(METAPLEX_PROGRAM), bytes(mint.pubkey())],
    METAPLEX_PROGRAM
)


creator = bytes(payer.pubkey())
creator1 = payer.pubkey()
print("+++++++++++++++++++++++++++++")
print(creator1)
print("+++++++++++++++++++++++++++++")

name = "World War"
symbol = "WW3"
uri = metadaturi
# ---- Create Instruction ----
create_discriminator = bytes([24, 30, 200, 40, 5, 28, 7, 119])
name_buf = pack("<I", len(name)) + name.encode()
symbol_buf = pack("<I", len(symbol)) + symbol.encode()
uri_buf = pack("<I", len(uri)) + uri.encode()
create_data = create_discriminator + name_buf + symbol_buf + uri_buf + creator

create_ix = TransactionInstruction(
    program_id=PUMP_FUN_PROGRAM,
    data=create_data,
    accounts=[
        AccountMeta(pubkey=mint.pubkey(), is_signer=True, is_writable=True),
        AccountMeta(pubkey=mint_auth_pda, is_signer=False, is_writable=False),
        AccountMeta(pubkey=bonding_curve_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=assoc_bonding, is_signer=False, is_writable=True),
        AccountMeta(pubkey=global_pda, is_signer=False, is_writable=False),
        AccountMeta(pubkey=METAPLEX_PROGRAM, is_signer=False, is_writable=False),
        AccountMeta(pubkey=metadata_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=ASSOCIATED_TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSVAR_RENT_PUBKEY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=EVENT_AUTHORITY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False),
    ]
)

# ---- Compute Budget ----
compute_ixs = [
    set_compute_unit_limit(500_000),
    set_compute_unit_price(1_000_000),
]

# ---- Optional: create ATA if doesn't exist ----
acct_info = client.get_account_info(assoc_user).value

ata_ix = None
if acct_info is None:
    ata_ix = create_associated_token_account(payer.pubkey(), payer.pubkey(), mint.pubkey())
   
# ---- Buy Instruction ----
amount = 19000000
#amount = int(0.1 * 1000000000)
amount = amount*1000000
slippage = 100
max_cost = (amount * (10000 + slippage)) // 10000

buy_discriminator = bytes([102, 6, 61, 18, 1, 218, 235, 234])
buy_data = buy_discriminator + pack("<Q", amount) + pack("<Q", max_cost)
creator_pubkey = creator1
creator_vault_pda, _ = Pubkey.find_program_address(
            [b"creator-vault", bytes(creator_pubkey)],
            PUMP_FUN_PROGRAM
)

buy_ix = TransactionInstruction(
    program_id=PUMP_FUN_PROGRAM,
    data=buy_data,
    
    accounts=[
        AccountMeta(pubkey=global_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=FEE_RECIPIENT, is_signer=False, is_writable=True),
        AccountMeta(pubkey=mint.pubkey(), is_signer=False, is_writable=False),
        AccountMeta(pubkey=bonding_curve_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=assoc_bonding, is_signer=False, is_writable=True),
        AccountMeta(pubkey=assoc_user, is_signer=False, is_writable=True),
        AccountMeta(pubkey=payer.pubkey(), is_signer=True, is_writable=True),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=creator_vault_pda, is_signer=False, is_writable=True),
        AccountMeta(pubkey=EVENT_AUTHORITY, is_signer=False, is_writable=False),
        AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False),
    ]
)


ixs = compute_ixs + [create_ix]
if ata_ix:
    ixs.append(ata_ix)
ixs.append(buy_ix)

latest_blockhash = client.get_latest_blockhash().value.blockhash

msg = MessageV0.try_compile(
    payer.pubkey(),
    ixs,
    [],  # address lookup tables
    Hash.from_string(str(latest_blockhash)),
)


tx2 = VersionedTransaction(msg, [payer, mint])

tx3 = create_buy_transaction(
    mint_address=str(mint.pubkey()),
    token_amount=18000000,  
    recent_blockhash=str(latest_blockhash),
    creator_vault_pda = creator_vault_pda
)

tx4 = create_buy_transaction2(
    mint_address=str(mint.pubkey()),
    token_amount=17000000,  
    recent_blockhash=str(latest_blockhash),
    creator_vault_pda = creator_vault_pda
)


tx5 = create_buy_transaction3(
    mint_address=str(mint.pubkey()),
    token_amount=15000000,  
    recent_blockhash=str(latest_blockhash),
    creator_vault_pda = creator_vault_pda
)





def basic_bundle():
    solana_client = Client("https://mainnet.helius-rpc.com/?api-key=bad4333f-cf37-4521-8a24-6a182bb0e579")

    jito_client = JitoJsonRpcSDK(url="https://mainnet.block-engine.jito.wtf/api/v1")
    blockhash = latest_blockhash
    jito_tip = Pubkey.from_string("96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5")
    def make_msg_v0(instructions):
        account_keys = [sender]
        accounts = []

        for ix in instructions:
            if ix.program_id not in account_keys:
                account_keys.append(ix.program_id)
            for meta in ix.accounts:
                if meta.pubkey not in account_keys:
                    account_keys.append(meta.pubkey)
                    accounts.append(meta)

        compiled = [
            CompiledInstruction(
                program_id_index=account_keys.index(ix.program_id),
                accounts=bytes([account_keys.index(m.pubkey) for m in ix.accounts]),
                data=ix.data
            ) for ix in instructions
        ]

        header = MessageHeader(1, 0, len([a for a in accounts if not a.is_writable]))
        return MessageV0(header, account_keys, blockhash, compiled, [])

    # ✅ Transaction 1: Tip to Jito
    tx1 = VersionedTransaction(
        make_msg_v0([
            transfer(TransferParams(from_pubkey=sender, to_pubkey=jito_tip, lamports=10000))
        ]),
        [jito_tip_keypair]
    )

    

    # Bundle and send
    bundle = [base64.b64encode(bytes(tx)).decode() for tx in [tx1, tx2, tx3, tx4, tx5]]
    #bundle = [base58.b58encode(bytes(tx)).decode() for tx in [tx1,tx2]]
    print("📦 Sending bundle with 3 transactions...")

    try:
        # response1 = client.simulate_transaction(tx2, commitment=Confirmed)
        # print(f"Simulation logs: {response1.value.logs}")
        result = jito_client.send_bundle(bundle)
        print("Raw API response:", json.dumps(result, indent=2))
    except Exception as e:
        print("❌ Error sending bundle:", e)

    

basic_bundle()
