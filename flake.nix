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
        # uv manages the virtual environment automatically
        shellHook = ''
          echo "[nix] uv environment ready - run 'uv sync' to install dependencies"
        '';
      };
    };
}
