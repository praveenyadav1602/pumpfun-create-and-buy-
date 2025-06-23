import json
import os
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0, MessageHeader
from solders.instruction import Instruction, AccountMeta, CompiledInstruction
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from spl.token.instructions import create_associated_token_account, get_associated_token_address
from spl.token.constants import TOKEN_PROGRAM_ID, ASSOCIATED_TOKEN_PROGRAM_ID
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from struct import pack, unpack
from solders.system_program import TransferParams, transfer
from solders.sysvar import RENT as SYSVAR_RENT_PUBKEY
from solders.hash import Hash
import base58

        
def load_key(label, filename="allkeys.txt"):
    with open(filename, "r") as f:
        for line in f:
            if line.strip().startswith(label):
                # Extract value between quotes
                key = line.split("=")[1].strip().strip('"')
                return key
    raise ValueError(f"Label '{label}' not found in {filename}")

# Get the base58 private key for 'addwall1'
base58_private_key = load_key("addwall2")
decoded = base58.b58decode(base58_private_key)
payer = Keypair.from_bytes(bytes(decoded))    

rpc_endpoint = "https://mainnet.helius-rpc.com/?api-key=bad4333f-cf37-4521-8a24-6a182bb0e579"
slippage = 100  # 1% slippage

# Program constants
PUMP_FUN_PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
FEE_RECIPIENT = Pubkey.from_string("62qc2CNXwrYqQScmEdiZFFAnJR262PxWEuNQtxfafNgV")
EVENT_AUTHORITY = Pubkey.from_string("Ce6TQqeHC9p8KetsN6JsjHK7UTZk7nasjjnr7XxXp9F1")
SYSTEM_PROGRAM_ID = Pubkey.from_string("11111111111111111111111111111111")
COMPUTE_BUDGET_PROGRAM_ID = Pubkey.from_string("ComputeBudget111111111111111111111111111111")

def create_buy_transaction2(
    mint_address: str,
    token_amount: int,
    recent_blockhash: str,
    creator_vault_pda: str
) -> VersionedTransaction:
    """Main function that takes only the 3 parameters you want to pass"""
    payer_pubkey = payer.pubkey()
    client = Client(rpc_endpoint)
    MINT_ADDRESS = Pubkey.from_string(mint_address)

    # Derive PDAs
    def derive_pda(seeds: list, program_id: Pubkey) -> Pubkey:
        return Pubkey.find_program_address(seeds, program_id)[0]

    global_pda = derive_pda([b"global"], PUMP_FUN_PROGRAM)
    bonding_curve_pda = derive_pda([b"bonding-curve", bytes(MINT_ADDRESS)], PUMP_FUN_PROGRAM)
    
    
    assoc_bonding = get_associated_token_address(bonding_curve_pda, MINT_ADDRESS)
    assoc_user = get_associated_token_address(payer_pubkey, MINT_ADDRESS)
   
    
    # Build buy instruction
    def build_buy_instruction(amount: int, max_cost: int, user: Pubkey) -> Instruction:
        buy_discriminator = bytes([102, 6, 61, 18, 1, 218, 235, 234])
        buy_data = buy_discriminator + pack("<Q", amount) + pack("<Q", max_cost)

        global_pda, global_bump = Pubkey.find_program_address(
            [b"global"],
            PUMP_FUN_PROGRAM
        )

        creator_pubkey = Pubkey.from_string("wDcZn6b7DgB8bsB9eyoDF4e3oKoMZZ2q6tFKHDQrzEy")

        accounts = [
            AccountMeta(pubkey=global_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=FEE_RECIPIENT, is_signer=False, is_writable=True),
            AccountMeta(pubkey=MINT_ADDRESS, is_signer=False, is_writable=False),
            AccountMeta(pubkey=bonding_curve_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=assoc_bonding, is_signer=False, is_writable=True),
            AccountMeta(pubkey=assoc_user, is_signer=False, is_writable=True),
            AccountMeta(pubkey=user, is_signer=True, is_writable=True),  
            AccountMeta(pubkey=SYSTEM_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
            AccountMeta(pubkey=creator_vault_pda, is_signer=False, is_writable=True),
            AccountMeta(pubkey=EVENT_AUTHORITY, is_signer=False, is_writable=False),
            AccountMeta(pubkey=PUMP_FUN_PROGRAM, is_signer=False, is_writable=False),
        ]

        return Instruction(
            program_id=PUMP_FUN_PROGRAM,
            accounts=accounts,
            data=buy_data
        )


    
    
    compute_ixs = [
        set_compute_unit_limit(500_000),
        set_compute_unit_price(1_000_000),
    ]
    
    acct_info = client.get_account_info(assoc_user).value
    ixs = compute_ixs
    
    if acct_info is None:
        ata_ix = create_associated_token_account(
            payer=payer_pubkey,
            owner=payer_pubkey,
            mint=MINT_ADDRESS
        )
        ixs.append(ata_ix)
    max_cost = 100000000000000000
    ntoken_amount = token_amount * 1000000
    buy_ix = build_buy_instruction(ntoken_amount, max_cost, payer_pubkey)
    ixs.append(buy_ix)
    
    msg = MessageV0.try_compile(
        payer=payer_pubkey,
        instructions=ixs,
        address_lookup_table_accounts=[],
        recent_blockhash=Hash.from_string(recent_blockhash),
    )
 
    return VersionedTransaction(msg, [payer])
    
