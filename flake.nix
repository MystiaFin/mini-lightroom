{
  description = "Mini-Lightroom Dev Environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShells.${system}.default = pkgs.mkShell {
        name = "mini-lightroom-shell";

        packages = [
          (pkgs.python3.withPackages (python-pkgs: [
            python-pkgs.opencv4
            python-pkgs.numpy
						python-pkgs.pillow
						python-pkgs.matplotlib
          ]))
          
          pkgs.black
        ];

        shellHook = ''
          echo "Python version: $(python --version)"
        '';
      };
    };
}
