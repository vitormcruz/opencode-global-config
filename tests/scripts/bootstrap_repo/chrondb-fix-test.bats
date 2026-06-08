#!/usr/bin/env bats
# tests/scripts/bootstrap_repo/chrondb-fix-test.bats

load "../../helpers/test_helper"

FIX_FUNC='
fix_chrondb_lib() {
  local chrondb_lib="${HOME}/.chrondb/lib"
  local tmp_dir="${chrondb_lib}/.tmp-extract-runtime"
  if [ -d "$tmp_dir" ] && [ -f "${tmp_dir}/libchrondb.so" ]; then
    say "            Corrigindo estrutura do chrondb..."
    mv "${tmp_dir}"/* "${chrondb_lib}/" 2>/dev/null
    rmdir "$tmp_dir" 2>/dev/null
  fi
}
say() { printf "%s\n" "$*"; }
'

setup() {
  common_setup
}

teardown() {
  common_teardown
}

@test "fix_chrondb_lib: move arquivos de .tmp-extract-runtime para lib/" {
  local chrondb_lib="$TEST_HOME/.chrondb/lib"
  local tmp_dir="${chrondb_lib}/.tmp-extract-runtime"
  mkdir -p "$tmp_dir"

  printf '#ifndef LIBCHRONDB_H\n#define LIBCHRONDB_H\n#endif\n' > "${tmp_dir}/libchrondb.h"
  printf '\0' > "${tmp_dir}/libchrondb.so"
  printf '/* header */\n' > "${tmp_dir}/graal_isolate.h"
  printf '/* header */\n' > "${tmp_dir}/graal_isolate_dynamic.h"
  printf '/* header */\n' > "${tmp_dir}/libchrondb_dynamic.h"

  run bash -c "
    HOME='$TEST_HOME'
    ${FIX_FUNC}
    fix_chrondb_lib
  "

  assert_success
  [ -f "${chrondb_lib}/libchrondb.h" ]
  [ -f "${chrondb_lib}/libchrondb.so" ]
  [ -f "${chrondb_lib}/graal_isolate.h" ]
  [ -f "${chrondb_lib}/graal_isolate_dynamic.h" ]
  [ -f "${chrondb_lib}/libchrondb_dynamic.h" ]
  [ ! -d "$tmp_dir" ] || fail "tmp_dir should not exist after fix"
}

@test "fix_chrondb_lib: nao faz nada quando dir nao existe" {
  local chrondb_lib="$TEST_HOME/.chrondb/lib"
  rm -rf "$chrondb_lib"

  run bash -c "
    HOME='$TEST_HOME'
    ${FIX_FUNC}
    fix_chrondb_lib
  "

  assert_success
  [ ! -d "$chrondb_lib/.tmp-extract-runtime" ]
}

@test "fix_chrondb_lib: nao faz nada quando arquivos ja estao em lib/" {
  local chrondb_lib="$TEST_HOME/.chrondb/lib"
  mkdir -p "$chrondb_lib"

  printf 'existing' > "${chrondb_lib}/libchrondb.so"

  run bash -c "
    HOME='$TEST_HOME'
    ${FIX_FUNC}
    fix_chrondb_lib
  "

  assert_success
  [ -f "${chrondb_lib}/libchrondb.so" ]
  [ "$(cat "${chrondb_lib}/libchrondb.so")" = "existing" ]
}

@test "fix_chrondb_lib: funcao existe no script wsl-install-deps" {
  run bash -c "grep -q 'fix_chrondb_lib' '$REPO_ROOT/scripts/bootstrap_repo/wsl-install-deps.sh'"
  assert_success
}