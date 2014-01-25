#include "sodium/crypto_hash.h"
#include "lua.h"

int l_crypto_hash(lua_State* L) {
    size_t inlen = 0;
    static char outbuf[crypto_hash_BYTES];
    const char* in = lua_tolstring(L, 0, &inlen);
    crypto_hash(outbuf,in,inlen);
    lua_pop(L, 1);
    lua_pushlstring(L, outbuf, crypto_hash_BYTES);
    return 1;
}

#define SELFMETA { lua_pushvalue(L,-1); lua_setmetatable(L,-2); }

int luaopen__sodium(lua_State* L) {
    // this will be sodium.* (t1)
    lua_createtable(L, 0, 2); // t1
    // this will be sodium.hash.* (t2)
    lua_createtable(L, 0, 1); // t1 t2
    // this will be metatable for sodium.hash
    lua_createtable(L, 0, 1); // t1 t2 t3
    lua_pushliteral(L,"__call"); // t1 t2 t3 __call
    lua_pushcfunction(L, l_crypto_hash); // t1 t2 t3 __call <func>
    lua_settable(L, -3); // t1 t2 t3(.__call=)
    lua_setmetatable(L,-2); // t1 t2(meta=t3)
    lua_pushliteral(L, "size"); //t1 t2 size
    lua_pushinteger(L, crypto_hash_BYTES); //t1 t2 size <int>
    lua_settable(L, -3); // t1 t2(.size=)
    lua_pushliteral(L, "hash"); // t1 t2 hash
    lua_insert(L,-2); // t1 hash t2
    lua_settable(L,-3); // t1(.hash=t2)
    return 1; // t1
}
