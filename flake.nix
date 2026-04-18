{
  description = "Python template: Flask";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python312
          uv
          sqlite
          openssl
          libffi
          pkg-config
          gcc
        ];

        shellHook = ''
          VENV_DIR=".venv"
          STAMP_FILE="$VENV_DIR/.requirements.sha256"
          EXPECTED_PYTHON="${pkgs.python312}/bin/python3.12"
          EXPECTED_VERSION="$($EXPECTED_PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

          CURRENT_VERSION=""
          if [ -x "$VENV_DIR/bin/python" ]; then
            CURRENT_VERSION="$($VENV_DIR/bin/python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || true)"
          fi

          if [ ! -x "$VENV_DIR/bin/python" ] || [ "$CURRENT_VERSION" != "$EXPECTED_VERSION" ]; then
            if [ -d "$VENV_DIR" ] && [ "$CURRENT_VERSION" != "$EXPECTED_VERSION" ]; then
              echo "[nix] Recreating $VENV_DIR to match Python $EXPECTED_VERSION"
              rm -rf "$VENV_DIR"
            fi
            echo "[nix] Creating virtual environment in $VENV_DIR"
            "$EXPECTED_PYTHON" -m venv "$VENV_DIR"
          fi

          REQ_HASH="$(sha256sum requirements.txt | awk '{print $1}')"
          INSTALLED_HASH=""
          if [ -f "$STAMP_FILE" ]; then
            INSTALLED_HASH="$(cat "$STAMP_FILE")"
          fi

          if [ "$REQ_HASH" != "$INSTALLED_HASH" ]; then
            echo "[nix] Installing/updating Python dependencies from requirements.txt"
            if PYTHONPATH="" "$VENV_DIR/bin/python" -m pip install -r requirements.txt; then
              echo "$REQ_HASH" > "$STAMP_FILE"
            else
              echo "[nix] Dependency installation failed; keeping previous environment state" >&2
            fi
          fi

          unset PYTHONPATH
          export PATH="$PWD/$VENV_DIR/bin:$PATH"
          hash -r
          echo "[nix] Virtualenv ready: $VENV_DIR (python: $(command -v python))"
        '';
      };
    };
}
