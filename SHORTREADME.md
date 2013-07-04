With email you have to encode binary attachments in text format, can't link to other emails, have no way to sign headers, can't whitelist, can't distribute the load, can't verify signatures until downloading the entire email including attachments, can't load only part of the email's body into memory, and when you sign them you sign the quoted-printable encoding not the original message.

So I thought I'd fix that.

I think the best idea is using a hash tree to represent files, files being emails, documents, attachments, whatever. To make a hash tree you divide a file into pieces of a fixed arbitrary maximum size, take the hash of each of those pieces, and combine them into a list. That list itself considered a file can go through the algorithm recursively, until the file you're dealing with is smaller than a single piece. 

As an example, let's say O is some data and x is a hash, and each piece can take as many as 3 O's
You start with a file:
<pre>
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
</pre>
...and split it into pieces
<pre>
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
OOO OOO OOO OOO OOO O
</pre>
Notice the last piece is short, because the file isn't evenly divisible by 3 O's.
Now you take the hash of each of those pieces, OOO -&gt; x, thus:
<pre>
x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x
</pre>
Concatenate those together, and you've got
<pre>xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</pre>
...which is smaller than the original file!

Now recurse. (aka lather, rinse, repeat)
<pre>OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
-&gt;
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
-&gt;
x x x x x x x x x x
-&gt;
xxxxxxxxxx
-&gt;
OOOOOOOOOO
-&gt;
OOO OOO OOO O
-&gt;
x x x x
-&gt;
xxxx
-&gt;
OOOO
-&gt;
OOO O
-&gt;
x x
-&gt;
xx
-&gt;
OO
-&gt;
x
</pre>

And now you've got a single hash that uniquely represents the entire file. Since it is calculated in a tree structure, you can follow down the individual tree branches, verifying along the way, and thus verify the contents of the file piece-wise. Linking between files is trivial since the root hash is a "content hash key" and will (hopefully) be unique for every distinct file. Instead of implementing signatures as a hash of the entire file encoded to an arbitrary quoted-printable format, added at the end, you can start with the signature, which signs the root hash, and you can decide whether to read, or even download a message depending on who signed it.

Note you need to know the depth of the tree as well as the root hash, otherwise you'd consider the pieces of the file as being hashes to something else!

What I'm working on now is encrypting a hash tree. I've got it so each node has the same "counter" in both insertion and extraction. Applying that to a base nonce, then using a previously known encryption key, you can safely encrypt each piece using the CTR method. Once you have the root hash of those encrypted pieces, then you can make a tiny file to carry the information needed to decrypt thus:
<pre>
nonce + encrypted(friend1,000 + secretKey + rootHash) + encrypted(friend2, 000 + secretKey + rootHash) + ...
</pre>
...and upon getting the root hash of <i>that</i>, you can distribute it to each of your friends, without worry about what arbitrary party gets their hands on it. By adding dummy slots you can disguise how many friends you are contacting, and each friend can only see the particular slot for their own key.

Public keys are just inserted as files, and their root hash used as their unique identifier, fingerprint so to speak. To make signatures you do this:
<pre>
myPublicKeyHash + encrypted(myPrivateKey, 000 + rootHash)
</pre>
"encrypted" in this case is a misnomer, since signing is slightly different from encryption to prevent certain attacks that change the data without invalidating the signature. Anyway this information itself is <i>not</i> put into a hash tree, because it's a catch-22 to try to sign a signature, and you should just send the signature pieces around blindly. I can't think of any other way to do it. You could have "feeds" or "streams" that people subscribe to which get regularly fed signatures, and depending on who signs it they can then descend into the hash tree.

Metadata, MIME type, filename and such could be stored in a file, along with the root hash, which itself would produce a root hash. Links within the files would be abstracted above the hash tree structure, and would only be followed once you verify that (part) of the file.

Could just put all the pieces in a Kademlia DB, or probably better a Kademlia DB of hash:location pairs, and an arbitrary network for exchanging the actual pieces. Could just make a text file with a list of your favorite files and their root hashes.

There's a limit to the depth of recursion obviously, but 4 is more than enough for a hash tree of even huge files, and atop that metadata/signature pieces will be well within a single byte depth counter. Furthermore since I insert with an algorithm similar to addition, once a list of pieces "carries up" it can be freed, so only one branch of the tree needs to be allocated at any given time. Should scale well.
