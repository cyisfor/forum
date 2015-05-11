Email has problems. On state of the art hardware, it still takes me 20 seconds at least to load up some image attachments. It doesn’t have built-in signing, and the MIME format is quite possibly the most difficult encoding to optimize that I’ve ever seen. So we need to fix it. The right way, instead of just half-baked hacks on top of a hastily constructed anti-pattern.

The idea is this: if you take _a lot_ of data, you can put it through a cryptographic hash to get _a little bit_ of data. The big problem with email is that you have to remain blindly trusting of _a lot_ of data, which sets you up for being spammed, flooded, and dependent on large corporations who alone have the power and knowhow to deal with that much strange, unvetted data.

You don’t even _want_ to download most of this “a lot” of data though. And what you do want to download, you want to do incrementally, in a way you can verify in case it got messed up or modified. Wouldn’t it be better if you just downloaded a teeny little message summary, that you can use to filter out the emails from people you don’t know? If that’s the only data you accept blindly, and you explicitly request all the big emails and attachments, then email will be easier to manage for you, for server administrators, and for your recipients.

So, there’s a way to only download big data by request, yet still receive emails without requesting them beforehand. That ways is hash trees, and digital signatures. What you get is a digital signature of a cryptographic hash, and that’s _a little bit_ of data. From there you can tell who sent you the email, without seeing a single byte of the actual message, or its attachments. Using this signature you can verify who’s telling you this is a message worth reading, and using the cryptographic hash you can request the message fully confident that it is exactly what your friend wrote, pointed out, assembled or forwarded.

There is still a problem though. Given a big fat email, and a cryptographic hash, you can tell whether that email is _the_ email for that hash. But without downloading the big fat email, how are you going to tell whether it’s the right email? The answer is hash trees.

Hashing is sort of like, there’s a function H (sha256 or something) that uses fancy math on a bunch of bytes: the content of your message, for instance. Once it has digested those bytes, it produces a tiny little string of 32 bytes. So if you have a megabyte of data A, and a hash function H, you can be sure that H(A) is only going to be 32 bytes. If someone sends you H(A), and then sends you A, and they haven’t kept their hash function secret (sha256 for instance is as public as all get out), then you can calculate H(A) too, and compare it with the H(A) that they sent you.

This is good because people like to mess with email. If I just sent an email to some random person I didn’t know, and they were supposed to send it to you, they could change my words, or more likely start bombing you with spam, and you’d have no way to tell whether it was the spammer’s email, or mine. But if you have H(A) and I send you A, and then some evil spammer sends you B, C, D and E, all with my return address on them, you can figure out H(B), and H(B) will always be different from H(A). Thereby your computer can just delete B without trouble. In fact, if I’m sending you A from a different source than the spammer, you can just block the spammer’s IP before they even get a chance to send you C, D and E.

In the end, your Inbox has just one email, the contents of A.

Email already has hashing, in the form of PGP, but that too has a problem. I said you could cut off the spammer before C, D and E, but that’s only if those are separate messages. If the spammer sends you a big BCDE message, you’ll have to download and save every byte of it, before you can calculate H(BCDE), and discover that it’s not H(A) as you expected. This limits the feasible size of email, so if I want to send you anything significant, well I just can’t, because if I have 200 megabytes to send you, you can’t tell whether or not I’m the spammer until that 200 megabytes has been received.

There is seriously no solution to this. You can’t verify a hash without the whole big data that it hashes. That’s just a mathematical fact. What I’m trying to do is something sneaky to get around that limitation, which I call hash trees.

Let’s say I want to send you a big email called ABCDE. (It’s not spam, I promise.) You don’t want to wait for the entire email before you can tell whether it’s my cute cat video, and not someone else’s commercial selling illegal painkillers to desperate addicts. Wouldn’t it be better if I split up the email, and sent you it in the form of A, then B, then C, and so on? You can start out with H(ABCDE), and then you need the entire message, but if you start out instead with H(A), H(B), H(C), and so on, then you can verify it _piecewise_. So if I send you ABCDE, and someone else sends you an unsolicited CDEFG, you can cut that person off at the C, without banning me from sending you any emails bigger than A. You limit your accepted email size to something small, but then you stitch the several small emails I send together to get a big email in the end.

You might be asking where are you going to get these hashes in the first place, and that’s something about digital signatures, but for now just assume you _can_ get the hashes, and beyond that you can limit the big emails you get sent. Unless it’s your friend, whereupon they split up the email, and you stitch it back together.

Here's an example. We got a file that's nothing but O's. We have a hash function that turns a file into one letter ‘x’. This is a bad hash function since it verifies every piece, but just for purposes of demonstration imagine that if A = OOOOOOOOOOOO, then H(A) = x.

Let’s say you set your maximum email size to 3 letters. Pretty small, but demonstration purposes etc. Here’s what I want to send you:

<pre>
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
</pre>

...and what I can do is split it into pieces:
<pre>
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
OOO OOO OOO OOO OOO O
</pre>

Notice the last piece is shorter than 3 letters, because the file isn't evenly divisible by 3.

Now I take the hash of each of those pieces, A OOO -> H(A) x, thus:
<pre>
x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x
</pre>
Concatenate those together, and I’ve got
<pre>xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</pre>
or more aptly
<pre>OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO</pre>
...which is smaller than the original file!

If I can send you <code>OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO</code> then you can ask me for each of the OOO pieces one at a time, without accepting all that III spam. But <code>OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO</code> is still too big! Your limit is three letters! Now what do we do?

This is where it's called a hash tree. Now I have a smaller file, that can help you validate the bigger file. But the smaller file is still too big for you to trust without validating it. How do you validate the smaller file? Recursion is the answer! I split the _second_ file to split into pieces:
<pre>
->
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
->
x x x x x x x x x x
->
xxxxxxxxxx
 = 
OOOOOOOOOO
</pre>

By repeating this process, we can continue reducing until our file is smaller than the maximum piece size. Then the entire file can be treated as a single piece (the "root" piece) and its corresponding hash the root hash, can uniquely identify all the levels down to the original file.

So all at once:
<pre>
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
->
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
OOO OOO OOO OOO OOO O
->
x x x x x x x x x x x x x x x x x x x x x x x x x x x x x x
->
xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
 =
OOOOOOOOOOOOOOOOOOOOOOOOOOOOOO
->
OOO OOO OOO OOO OOO OOO OOO OOO OOO OOO
->
x x x x x x x x x x
->
xxxxxxxxxx
 =
OOOOOOOOOO
->
OOO OOO OOO O
->
x x x x
->
xxxx
 =
OOOO
->
OOO O
->
x x
->
xx
 =
OO
->
x
 =
O 
</pre>

Why is all this a good thing? Well, you can make sure you're getting what you asked for. You've done the search on Gnutella, and got 7 strangely sized files with your exact keywords that all end in .exe. If you have the root hash, that O on the bottom, then you can check whether the file you're receiving is the one you want, or one of the 6 zillion virus traps out there.

Why would your friends send you viruses? Here's the thing: with this system you <i>don't have to interact only with your friends.</i> I like to use the Hitler analogy for this. Let's say you've got Hitler in a position of power such that he gets every email you send, except for a tiny 32 bytes. Now he could refuse to deliver those emails, because he's an evil cookie cutter villain, but he could also <i>change</i> them. You said to meet under the bridge, but what reaches your friend says to swear allegience to the Fuher. (On a serious note the Nazis were masters of propaganda, which is possiby the biggest reason they got so far.) Now your friend knows you wouldn't say that, right? But here's an email from you with those very words. Maybe he will question you the next time your resolve is tested? Maybe he will falter at a crucial moment?

If there was a way for your friend to check, to <i>verify</i> that this was the same thing you sent, then there would be no question that it was yours. That might seem silly for emails, but for contracts, checks, tax documents, and other important stuff like that, this verification is essential.

So that's why you use hashes. You send the hash over the only 32 bytes Hitler doesn't control, and now his only choice is to send the actual message, or simply not send anything. Your friend can tell if what's in it is bogus. Thankfully we don't all live in a police state where our every interaction with each other is carefully controlled and monitored. If you are convicted and imprisoned, hashes won't do much to help you. But if you have that _little_ degree of freedom to exchange information, then you can use broad channels run by powerful corporations or even tyrannical dictators, and that data will remain sacrosanct.

Now here's a trick, what if you could send someone a bit of data <i>before</i> Hitler stole your email server, but after that you could send <i>no</i> data that was unmanipulable. Not even 32 bytes! Then there's a problem, because when you send your friend the hash x, Hitler can possibly intercept this, and replace it with y. Now suddenly your friend is watching busty women in square caps killing Jews, while rejecting the pieces <i>you</i> are sending, because you are sending stuff that resolves to x, and Hitler tricked them into thinking you were sending y. This is called a "middle man" attack, and can be quite scary. It's not as big a problem as it seems though, because as I said, the vast majority of us <i>don't</i> have a single giant authority controlling <i>everything</i> in our lives, just controlling <i>most</i> of it. As long as you can get that 32 bytes through, you'll never have to worry about fraud or trickery on the part of those hiding in secret between you and your friend.

And if you can’t even get that 32 bytes through _now_, if at any point in the past you _have_ been able to, then no middle man can fool you, no matter how much control they have.

Here's why middle man attacks are a seductive non-problem. Suppose Hitler breaks into my house, and points a Walther P38 at my head, and says "Do nein let anyone know im hir, type as normalzie." Now let’s say you're typing your secret message to me, and you have no way of knowing I've been co-opted by Hitler. I can’t exactly type “help hitler is pointing a gun at my head” without him shooting me after all. He's effectively middle manned me manually, with a pistol!

It's silly to refuse to do any communication unless you can account for pistol wielding, undead, zombie, werewolf dictators, thus it's silly to demand a complete stop to any middle man attacks. The goal I have is just to make them vanishingly difficult, but as with any security your safety will be a matter of degree more than black and white.

Back to the earlier premise. You can send your friend a bit of data unmangled, but only once, and after that your communication is ruefully fucked by immensely powerful monitors. How do you deal with this? The answer is asymmetric encryption, or “digital signing.”

That bit of data you send can be what's called a "public key". It's a very large number (in the form of a bunch of bytes) associated with another very large number called the "private key". I won't go into the math, but the end result is that you can encrypt data with either key, and data encrypted with your public key can <i>only</i> be decrypted by your private key. <i>Not</i> your public key! Similarly, anything encrypted with your private key can <i>only</i> be decrypted by <i>your</i> public key. That’s why they call it asymmetric. Symmetric encryption just has one key, and anything it encrypts, it can decrypt.

What you do is you send your friend your public key. In fact you send _everyone_ your public key. And you share your private key with *no one*. Then, Hitler sneaks in and takes over the world. Now, when you want to send something, you need your friend to get the hash of that something, but as I mentioned before Hitler can use a middle man attack to change the hash in place, and deceive your friend. What you do to stop this is, you encrypt the hash with your private key.

You remember that the one thing you were able to send was your public key, before even your hashes were corrupted by evil. But if your friend has that public key, what can they do with something you’ve encrypted with your private key? Decrypt it, of course!

I want to email you A, and Hitler wants to email you B. You have my public key P, and I have my private key E, and we both agree on hash function H. If I just send you H(A), Hitler will replace it with H(B), and you’ll request B, the email not from me. But if I send you E(H(A)), what is Hitler going to do? Notice I never ever sent my private key over the wire. In fact, private keys should never be shared under any circumstances, and become entirely useless when they are. Hitler can only monitor our communications, but thankfully isn’t powerful enough to put a gun to my head, so there’s no way for him to get my secret key E. If you get E(H(A)) and you try running P on it, P and E cancel out, so you end up with H(A) and request A. If you get H(B), running P on it won’t cancel out since it’s not wrapped in E, so Hitler can’t fool you there. And Hitler can’t send you E(H(B)) because without having my private key E, he can’t calculate E(anything).

To put it mildly, given digital signatures, Hitler is fucked.

And, that’s how we save email.

You want to receive emails, and you can’t know what they are beforehand, or what would be the point of sending them? But you don’t have to receive the entire email, or even a piece of it. All you need to receive is the digital signature of a root hash to a hash tree. When you get a queue of those, you can eliminate the ones signed by bad people, preserve the ones signed by good people, and ultimately limit the hardship everyone has to go through to get you the emails you want.

Only other aspect of email I wanted to fix is the abomination that is MIME. E-mail requires 7-bit encoding, which turns everything huge and is extremely difficult to decode. Massively difficult even. But with email in pieces like this, we have another option. If you reserve 2 bytes say, to store the size of a piece, followed by the bytes of the piece itself, that’s a binary encoding with very little waste. The trouble is, you can’t fit a size of greater than 65K in 2 bytes. But hey, we were breaking it up into pieces anyway, right? Why not 65K pieces?

Currently email is along the lines of this sort of syntax. First, count off every six _bits_, and save those into a byte, wasting 2 bits so that it’ll fit in a 7-bit encoding. (7 bits, for an 8-bit byte). This counting is very slow, because computers can only work in bytes at a time, so something _less_ than a byte that doesn’t _align_ with bytes, like say a sequence of 6 bit uh, thingies... it’s slow. Not only is it slow, you have to have two places for the file, one for its binary encoding, and one for the base64 crap which I just described.

That’s not the end of it though. Next you have to go through the text, and erase any lines that have only ‘.’ in them. This is because mbox requires ‘.’ be a separator between emails. So you have to go character by character through this text, carefully examining surrounding characters. that kind of parsing is ridiculously slow. You also have to eliminate any lines beginning with “From “ which is why in your emails you will sometimes see your sentence that begins with the word “From” replaced with “>From.”

No, that’s still not enough. Now you have to take this adjusted text, and this base64 6->8 junk, and concatenate them together, separating them with a “boundary.” This boundary is a sequence of random characters, which everyone just _really_ hopes won’t ever appear in the parts of the email. Nothing protecting your boundaries from being mismatched except faith and duct tape.

Then you have to stick a header on the front of each and every part of your email, and then a _second_ header on the top of the email. Then you put the whole thing into PGP to encrypt it, and you get (wait for it) MORE base64. Plus the lines “-- BEGIN ENCRYPTED DATA --” and stuff to waste even more bytes.

So now that we have email broken up into pieces, with a 2 byte size header that allows binary data, here’s what we can do. Your header is its own file, a sequence of pieces but more likely fits in a single piece. That header lists root hashes for the “parts” of the email. The message, any attachments, images, whatever. And that’s it. There are no attachments in this file, nothing embedded, no images. So where do you get them all?

Well, those images themselves can be broken down into small, efficient, easily processed pieces. Just like every attachment. Then, you just take the pieces of your header, the pieces of your attachments, and tack them all together into one big list of pieces. What “boundary” do we put between these pieces? None! Because since each piece has the size of itself at the beginning, nobody is ever going to be confused where one piece starts and the other stops.

My “email” format is thus:
SHHHMMMMMAAAAAAAAABBBBBBBBBCCCCCCC...

Each letter is a piece: a 2 byte size, followed by that many bytes of data. The first piece is a “signature” which lets you know who sent it. The only thing that signature contains is the root hash for the header. Then the pieces of the header are tacked on behind it, so you are sure to have the header to which that signature refers. HHH contains metadata and file names and subjects and topical stuff, keywords you can filter in or out. And if anyone uses bogus data for these fields, you just stop trusting their public key, and your problems will stop at the S.

So HHH contains topical stuff, and also a list of attachments, the first of which being the root hash for the email message MMMMM. MMMMM is just a file, well the pieces of a file tacked on the email, and it has a sort of HTML-ish format. I say HTML-ish because HTML is horrible and designed to force you to turn your computer over to corporate interests so they can take over your machine and force you to become more dependent on them. But a subset of HTML that allowed for markup like bold and italics, for embedded images and maybe videos, and most importantly allowed for links.

What’s a link? It’s a bit of text called a URL. (or a URI more generally). The big corporate fatheads like to say that a URL must start with their official corporate business name so that you can only have URLs that go to big businesses (and weird small organizations, but mostly big businesses). But there are other kinds of URL, and URI. “cid:” for instance, is a kind of URL that doesn’t point at a corporate business trademark brand name, but rather it just points to an attachment within the current email being viewed.

...unfortunately “cid:” is woefully unsupported in major email browsers. But it’s a step in the right direction. And now with hash trees we can do it right!

The email example ends with a bunch of attachments, each one being a collection of pieces that all add up to a root hash, one for each attachment. So if your root hash is “abcde” you could put “&lt;img name="kittens.jpg" type="image/png" src="cid:abcde"/&gt;” in your email, and then they’d see the image. Thus you can arrange your attachments how you like, and make a beautiful multi-media email that is efficient, secure, and considerate of the person you’re sending it to.

Now here’s the incredible thing. Root hashes are just 32 random-ish bytes. they aren’t just unique within a single email. They’re _globally_ unique. So let’s say I find an episode of a show I like, and send you a video about it. Remember you only get sent the ‘S‘ of the message without asking, and the rest of it you request as needed. You get the video and enjoy it, and I dunno, send a message to someone about how cool it is. But maybe I already sent the video to that someone. Are you going to send the video to them a second time?

According to email, the answer is yes!

According to hash trees, it’s a resounding no. In fact, this eliminates any problems with mass emails. Instead of copying around a 20 megabyte email full of stupid pet photos a thousand times, it only gets copied once for every recipient, and forwarding it to someone else on accident twice will only cost the cost of a tiny little digital signature.

Let’s say you sign an email. Does that mean you can be held legally accountable for anything written in it? According to PGP, the answer is (wait for it) yes!

According to my scheme, another resounding no. In fact, forwarding emails would be signed by you, just as much as ones you composed yourself. The fact is you can digitally sign just about anything, and while you want to sign good stuff  so people trust your key, if someone comes up waving a gun in your face and shouting about your plot to destroy the sanctity of national marriage Jesus, or something, the best they can tell is that you sent that email at one point, but there is no proof that you even wrote it.

Of course you _can_ attach proof, timestamps and all sorts of indicators that can’t be duplicated when someone copies your email. But with PGP that sort of thing is _mandatory_, and that makes it a bit unappealing for people who don’t want to be held legally accountable for everything they sign. Really, even with PGP you can still sign someone else’s email, so your signature proves nothing in court, but they have a sort of haughty attitude that their cryptography is some kind of moral fabric of society, so it’s easy to trick judges and police into thinking that there’s some magic compulsion keeping you from signing emails you didn’t write.

I’d try to fix that by making it unambiguous how little corellation there is between a signature and what it signs. You can get an idea of what will be produced by a given signature, but you can never determine what signature produced a given email. Digital signatures are great because they can help you filter out the bad people, and they don’t put you in danger since literally the only thing you’re signing is 32 random-ish bytes, which _just_ happen to be the root hash of a particular email.

Oh, hash trees can also be swarmed, like bittorrent. That’s different from emails, which must only be streamed.
