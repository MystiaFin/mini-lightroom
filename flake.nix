{
  description = "Mini Lightroom Python Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          name = "mini-lightroom-shell";
          
          packages = [
            (pkgs.python3.withPackages (ps: with ps; [
              numpy
              pillow
							matplotlib
            ]))
          ];

          shellHook = ''
            echo "Python: $(python --version)"
          '';
        };
      }
    );
}
