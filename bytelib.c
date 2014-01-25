#ifndef API
#       if defined _WIN32
#               define API __declspec(dllexport)
#       else
#               define API extern
#       endif
#endif

#include "lua.h"

static int word2s(lua_State *L) {
    lua_Integer n = lua_tointeger(L,1);
    char s[4];
    s[0] = n >> 6 & 0xFF;
    s[1] = n >> 4 & 0xFF;
    s[2] = n >> 2 & 0xFF;
    s[3] = n      & 0xFF;
    lua_pushlstring(L,s,4);
    return 1;
}

static int s2word(lua_State *L) {
    size_t len = 0;
    const char* s = lua_tolstring(L, 1, &len);
    if(len != 4) {
        lua_pushstring(L,"A word is 4 bytes");
        lua_error(L);
        return 0;
    }
    lua_pushinteger(L,s[0] << 6 | s[1] << 4 | s[2] << 2 | s[3]);
    return 1;
}

API int luaopen__bytelib(lua_State *L) {
    lua_createtable(L, 0, 2);
    lua_pushcfunction(L, word2s);
    lua_setfield(L, 2, "word2s");
    lua_pushcfunction(L,s2word);
    lua_setfield(L, 2, "s2word");
    return 1;
}

