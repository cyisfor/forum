So the idea is if you take a lot of data you can put it through a cryptographic hash to get a little bit of data. It's easier to transfer a little bit of data around, and thus harder for bullies or malcontents to keep you from getting it. The trouble is how much data is a lot of data? You still need to have all the bytes before you can calculate their hash. Until that happens, you have no idea whether you are receiving and storing garbled nothing, malicious code, or the file you want.

Email solves this by burying its head in the sand and telling you to just let Google take care of it.

So you want to hash a lot of data to get a little data, but not a <b>whole</b> lot of data. Thus a hash tree. Take a file you want to send someone, break it into pieces. Each piece can be "big" but doesn't have to be too big. There's an arbitrary maximum piece size, which could even change with network weather in the future. Pieces can be smaller than that, but not bigger.

Each of those pieces can be hashed, and if you put the hashes in order of the pieces they hash in the file, then you'll have a "hash list" which though much smaller than the file can completely verify its content, even if you only have part of the file.

This list of hashes can itself be considered a file then, and broken into pieces. 

So here's an example. We got a file that's O's. We have a hash that turns a piece into one x, and we set the maximum piece size to 3 O's. Here's the file:
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
...and here it is split into pieces
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO O
Notice the last piece is short, because the file isn't evenly divisible by 3 O's.
Now you take the hash of each of those pieces, OOO -> x, thus:

x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x

Concatenate those together, and you've got
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
...which is smaller than the original file!

This is where it's called a hash tree. Now you have a smaller file that can validate the bigger file. How do you validate the smaller file? Recursion is the answer! Now we have a file to split into pieces:
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
->
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
->
x x x x x x x x x x
->
xxxxxxxxxx

By repeating this process, we can continue reducing until our file is smaller than the maximum piece size. Then the entire file can be treated as a single piece (the "root" piece) and its corresponding hash the root hash, can uniquely identify all the levels down to the original file.

Why is this a good thing? Well, you can make sure you're getting what you asked for. You've done the search on Gnutella and got 7 strangely sized files with your exact keywords that all end in .exe. If you have the root hash, then you can check whether the file you're receiving is the one you want, or one of the 6 zillion virus traps out there.

Why would your friends send you viruses? Here's the thing: with this system you <i>don't have to interact only with your friends.</i> I like to use the Hitler analogy for this. Let's say you've got Hitler in a position of power such that he gets every email you send, except for a tiny 32 bytes. Now he could refuse to deliver those emails, because he's an evil cookie cutter villain, but he could also <i>change</i> them. You said to meet under the bridge, but what reaches your friend says to swear allegience to the Fuher. (On a serious note the Nazis were masters of propaganda, which is possiby the biggest reason they got so far.) Now your friend knows you wouldn't say that, right? But here's an email from you with those very words. Maybe he will question you the next time your resolve is tested? Maybe he will falter at a crucial moment?

If there was a way for your friend to check, to <i>verify</i> that this was the same thing you sent, then there would be no question that it was yours. That might seem silly for emails, but for contracts, checks, tax documents, and other important stuff like that, this verification is essential.

So that's why you use hashes. You send the hash over the only 32 bytes Hitler doesn't control, and now his only choice is to send the actual message, or simply not send anything. Your friend can tell if what's in it is bogus. Thankfully we don't all live in a police state where our every interaction with each other is carefully controlled and monitored. If you are convicted and imprisoned hashes won't do much to help you. But if you have that little degree of freedom to exchange information, then you can use broad channels run by powerful corporations or even tyrannical dictators, and that data will remain sacrosanct.

Now Hitler is pretty steamed about this. So instead of not sending your email, he starts sending your friend an unending email gigabytes long. Just the phrase "HITLERRULESSTALINDROOLS" repeated over and over again. He's doing this to waste your friend's hard disk space and CPU processing time, and there's not much your friend can do to stop it with hashes, because they need the entire file before they can verify it matches what you wanted to send, and Hitler just keeps on sending the file longer and longer!

Email solves this by setting a maximum size limit to any one email. That's why you can't share movies over email for instance. Or large PDFs. Or poster sized images. Yeah it sucks.

But with my hash tree method, you don't set a maximum size for the entire file. You set a maximum size for each <i>piece</i> of the file! That gives you the best of both worlds, in that your friend can verify what they've been sent without waiting for more than $maximumPieceSize to come in. That means if I try sending you a movie, and Hitler tries sending you SS porn, then you can accept and save my pieces, while Hitler's pieces never even touch your disk. The ability of me to send you files has no absolute size limit this way, limited only by time, and bandwidth.

Now here's a trick, what if you could send someone a bit of data <i>before</i> Hitler stole your email server, but after that you could send <i>no</i> data that was unmanipulable. Then there's a problem, because when you send your friend the hash x, Hitler can possibly intercept this, and replace it with y. Now suddenly your friend is watching busty women in square caps killing Jews while rejecting the pieces <i>you</i> are sending. This is called a "middle man" attack, and can be quite pernicious. It's not as big a problem as it seems though, because as I said the vast majority of us <i>don't</i> have a single giant authority controlling <i>everything</i> in our lives, just controlling <i>most</i> of it. As long as you can get that 32 bytes through you'll never have to worry about fraud or trickery on the part of those hiding in secret between you and your friend.

Here's why middle man attacks are a seductive non-problem. Suppose Hitler breaks into my house, and points a Walther P38 at my head, and says "Do nein let anyone know im hir, type as normalzie." Now you're typing your secret message to me and you have no way of knowing I've been co-opted by Hitler. He's effectively middle manned me manually with a pistol! It's silly to refuse to do any communication unless you can account for pistol wielding undead zombie werewolf dictators, thus it's silly to demand a complete stop to any middle man attacks. The goal I have is just to make them vanishingly difficult, but as with any security your safety will be a matter of degree more than black and white.

Back to the earlier premise. You can send your friend a bit of data unmangled, but only once, and after that your communication is ruefully fucked. How do you deal with this? The answer is asymmetric encryption. That bit of data you send can be what's called a "public key". It's a very large number (in the form of a bunch of bytes) paired with another very large number called the "private key". I won't go into the math, but the end result is that you can encrypt data with each key, and data encrypted with your public key can <i>only</i> be decrypted by your private key. <i>Not</i> your public key! Similarly anything encrypted with your private key can <i>only</i> be decrypted by <i>your</i> public key.

What you do is you send your friend your public key. Then Hitler sneaks in and takes over. Now when you want to send something, you need your friend to get the hash, but as I mentioned before Hitler can use a middle man attack to change the hash in place, and deceive your friend. What you do to stop this is you encrypt the hash with your private key. Now you only sent your public key over the wire, not your private key. Your private key is safe at home, where Hitler does not have the power to invade. And without your private key, obviously nobody can encrypt anything with your private key. They just don't have it! So Hitler can now either drop this data, without your friend getting any bad data, or can send it on unchanged, because if he changes it, here's what happens.

Your friend gets a message which is an encrypted hash, encrypted by your private key. Hitler replaced it with a quote from "Mein Kaumpf". When your friend decrypts the bogus message with your public key, they will get a hash, but it will be completely random and unpredictable. Junk data! Hitler will not be able to modify the message so that it produces a different hash, without knowing the private key. Sure he can read the message, since he has your public key just like anyone else, but he can't make that message seem to come from him. Thus even if Hitler controls your every 32 bytes on the line, your friend can decrypt this little message, and find the hash you originally intended, and there's nothing that Nazi bastard can do about it! Now that your friend undeniably has the correct hash, you can send them the pieces corresponding to its tree, free from worry that your friend might accidentally reject your pieces in favor of "Blood and Periods: a step by stiletto step guide to killing the Jews."

Obviously if Hitler can intercept even your public key then you're screwed. And if Hitler can steal your private key then you're screwed. But if you can keep your private key unseen by any besides you, and if you have the ability to communicate over a channel Hitler doesn't control <i>once</i>, then your files can be verified <i>for all time</i> afterwards! Again this doesn't work so well in prison, because when you tell the police "You aren't allowed to look at my private key so that I can receive secret messages and stop you from tampering with them," they just laugh and loosen their belt and tell you to bend over. But there are lots of situations where it <i>does</i> work well, and for those situations I think it's important that we follow these practices, and follow them <i>soon</i> as possible. Because the next Hitler is just around the corner, and if you never use public keys until then, you might just get both you and your friends sent to The Camps.

So I have secret message A and your public key B. I can make A + B = C, such that unless someone already has the secret message (A), there's no way for them to figure out what A is just from having B and C! Obviously addition doesn't have this property, but some algorithms do, and those you can use to protect yourself.

So that's pretty much my goal first to have a hash tree of every file, and second to have signatures that can distinguish files sent from one person by files sent from another, regardless of who actually ends up delivering them. This is a recursive algorithm, so it can get quite tricky especially with asynchronous programming, but I think I've managed to do it using the nice "deferred" library. My problem now is getting encryption working.

So, encryption you make a random key, then you encrypt that key with your friend's public key. Now nobody can decrypt that except your friend, so if you send it out into the wild, you can be sure only your friend knows it. Then you encrypt each piece in the hash tree with that key. When you take the hash of the encrypted root piece, you now have a root hash, about 32 bytes, and a random key. This is a symmetric key so anyone who has it can encrypt and decrypt, but since you hid it with your friend's <i>asymmetric</i> public key, the whole tree can be only seen by you and your friend. In fact if you fail to save the key yourself you won't be able to read it either!

Good encryption requires a nonce, that is a number used only once for a given key, for a given runthrough of the encryption algorithm. That number should be large, but only needs to vary a tiny bit from runthrough to runthrough to ensure data security. So what I did was generate a random "base" nonce, then give each piece a characteristic number that then gets combined with the base, to make a unique nonce per piece.

So you have the root hash for your friend's public key, a symmetric key, a nonce, and a root hash for the file you just encrypted, and you have to send that to your friend somehow. You save these all into a text <i>file</i> trying to figure out how best to send it.....

...that's right! You save the encryption information to a file, then turn that file into a hash tree! Generally the file will fit entirely in 1 piece, but that's fine because a hash tree of a file small enough to fit in one piece is nothing but the file itself (and a depth of 1). Of course you encrypt relevant stuff to your friend's public key first. you end up with something like:

nonce + encrypted(friendKey,secretKey + rootHash)

...stuffed into a piece. Then you send your friend the hash of that piece, and poof they can discover the key to decrypt the rest of it.

Want to send it to multiple friends? You don't have to insert the whole file multiple times, just encrypt the key + root several times! (I've been calling this a slot.)

nonce + encrypted(friend1,000 + secretKey + rootHash) + encrypted(friend2, 000 + secretKey + rootHash) + ...

Don't want Hitler to know how many friends you're messaging? Just pad the above file with random data. He doesn't have any of the private keys, so he can't tell which is random and which is an actual friend slot. In fact, neither can your friends! Currently I have it looking like you are sending everything to a multiple of 8 friends, regardless of if it's 8 or less, but that could easily become more granular or more fine. Each friend can tell which slot is theirs by checking the prefix, which is just a bunch of zeroes, but only when decrypted by the right key.

The way to do signatures is similar, where you and your friend exchange public keys, and then you want to send something certified. It's a good idea to sign every email in fact, so that nobody gets in the habit of trusting unsigned emails to be true. As the movie Equestria Girls shows, this can result in a lot of ruined friendships. What you send is a piece like this:

myPublicKey + encrypted(myPrivateKey, 000 + rootHash)

Your public key has a hash, which you send. Ostensibly your friend already has your public key. If not, send it to them! You can only start building a reputation if people have your public key. So they can look up your public key. The rest of the file is encrypted with your private key. So your friend tries to decrypt it with your public key, and they see a prefix of 000, so they know it worked! Then they can be sure rootHash leads to an email or other file that you "signed". Since nobody else has your private key, nobody can construct a message that your public key will decrypt. Anyone can decrypt the above signature, but only you can create it. And because of the magic of one way cryptographic hash functions, all you have to do is encrypt the root hash and the rest of the file cannot vary from what you expect them to receive.

Hashes are unique identifiers, and that's amazing for documents that bear links to each other. One thing you might notice about email is you can't link to another email. You have to actually paste that email into your own. There is rudimentary support for linking (which is why threads work at all) but how many times have you seen an email thread where the reply doesn't have any parent? Linking in emails is well in short pretty fucked up.

This is especially true of attachments. With email you cannot link to a specific attachment in another email. You have to re-attach that attachment to your new email. And here's the thing, all attachments have to be encoded in a way that makes them about 125% bigger, then concatenated into the email in a way that is practically impossible to parse without loading the entire email into memory. MIME is quite possibly the worst data format I've ever seen. It's even worse than XML!

...so when implementing email on top of this hash tree thing, I was hoping to have emails contain links to attachments and other emails, not encode and embed the attachment into the email body itself. hash trees can store binary encoding just fine so no re-encoding is needed, but it just makes more sense to link instead of embed. For one thing, many people can link to the same file without taking up more resources. For another thing, email applications like thunderbird can avoid pre-loading these attachments when from untrusted parties. With MIME, thunderbird has to load all the attachments into memory. With hash trees, thunderbird doesn't even have to download the attachments at all! This is even legally safer, in addition to technologically safer.

The big reason links are perfect for hash trees though is that every file can be reduced to one single 32 byte hash. That hash can then be just put inside the &lt;link href=...&gt; part, and it will be possible to write an email application that can download that attachment, regardless of where that attachment may be. Content based linking means that you'll never have to change your documents when someone moves house or gets a new domain name. URLs are terrible because they are not hashes, but instead they are <i>locators</i>, so they in no way guarantee what you'll find at that location. If I go to the bank and sign a cashier's check, the content hash is like my signature, or the unique number on the check. The URL is like the latitude and longitude at which I was standing when I signed it. What the hell good is that information?

Of course it's useful to know where I <i>might</i> be, but the content hash is sufficient to know what I <i>did</i>. Thus it's a better way to link documents. It's also less prone to surveillance, because once you have the documents attachments emails and such, you don't have to go looking for them anymore.
