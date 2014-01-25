import nacl.secret
import sys

key = b'A'*nacl.secret.SecretBox.KEY_SIZE
nonce = b'Q'*nacl.secret.SecretBox.NONCE_SIZE

plain = b'W'*0xffff
ctext = nacl.secret.SecretBox(key).encrypt(plain,nonce)

print(hex(len(ctext)),hex(len(ctext)-len(plain)),hex(len(nonce)))
sys.stdout = sys.stdout.detach()
sys.stdout.write(b'\n---\n')
sys.stdout.write(ctext)
