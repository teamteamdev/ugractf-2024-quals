with (import <nixpkgs> {});
stdenv.mkDerivation {
  name = "uzh-server";
  buildInputs = [(gradle.override { java = openjdk; }) openjdk];
}
