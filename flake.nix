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
        # Set up the virtual environment and activate it when the shell starts
        shellHook = ''
          if [ ! -x .venv/bin/python ]; then
            echo "[nix] Creating virtual environment in .venv"
            python -m venv .venv
          fi

          source .venv/bin/activate
          hash -r
          echo "[nix] Virtual environment active: $VIRTUAL_ENV"
        '';
      };
    };
}
