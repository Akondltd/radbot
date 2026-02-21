"""
Build script for the native fee configuration module.

Compiles fee_native.pyx to a platform-specific native binary:
  - Windows: fee_native.cpXXX-win_amd64.pyd
  - Linux:   fee_native.cpython-XXX-x86_64-linux-gnu.so
  - macOS:   fee_native.cpython-XXX-darwin.so

Prerequisites:
    pip install cython setuptools
    A C compiler (MSVC on Windows, gcc/clang on Linux/macOS)

Usage:
    python config/build_fee_native.py            # Build and verify
    python config/build_fee_native.py --verify   # Verify existing build only
"""

import glob
import os
import sys
import shutil
import subprocess
from pathlib import Path


def build():
    """Build the native module for the current platform."""
    try:
        import Cython
        print(f"Cython version: {Cython.__version__}")
    except ImportError:
        print("ERROR: Cython is required to build the native module.")
        print("Install with: pip install cython")
        sys.exit(1)

    config_dir = Path(__file__).parent.absolute()
    pyx_file = config_dir / "fee_native.pyx"
    setup_file = config_dir / "_temp_setup.py"

    if not pyx_file.exists():
        print(f"ERROR: {pyx_file} not found")
        sys.exit(1)

    print(f"Building native module from: {pyx_file}")
    print(f"Platform: {sys.platform}")
    print(f"Python:   {sys.version}")

    # Platform-specific compiler flags
    if sys.platform == "win32":
        compile_args = ["/O2"]
        link_args = []
    elif sys.platform == "darwin":
        compile_args = ["-O3", "-fPIC"]
        link_args = []
    else:
        compile_args = ["-O3", "-fPIC"]
        link_args = []

    setup_content = f'''
import sys
from setuptools import setup, Extension
from Cython.Build import cythonize

ext = Extension(
    name="fee_native",
    sources=["fee_native.pyx"],
    extra_compile_args={compile_args!r},
    extra_link_args={link_args!r},
)

setup(
    name="fee_native",
    ext_modules=cythonize(
        [ext],
        compiler_directives={{
            'language_level': 3,
            'boundscheck': False,
            'wraparound': False,
            'initializedcheck': False,
            'cdivision': True,
        }},
    ),
)
'''

    with open(setup_file, 'w') as f:
        f.write(setup_content)

    try:
        result = subprocess.run(
            [sys.executable, str(setup_file), "build_ext", "--inplace"],
            cwd=str(config_dir),
            capture_output=True,
            text=True
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:
            print(f"\nBuild failed with return code {result.returncode}")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("BUILD SUCCESSFUL")
        print("=" * 60)

        # Report built file
        built_files = (
            glob.glob(str(config_dir / "fee_native*.pyd")) +
            glob.glob(str(config_dir / "fee_native*.so"))
        )
        if built_files:
            for bf in built_files:
                print(f"  Built: {Path(bf).name}")
            print("\nThe native module is ready to use.")
            print("For distribution, delete fee_native.pyx and ship only the binary.")

        # Clean up intermediate build artifacts
        for pattern in ["fee_native.c", "*.o", "*.obj"]:
            for f in glob.glob(str(config_dir / pattern)):
                try:
                    os.remove(f)
                    print(f"  Cleaned: {Path(f).name}")
                except OSError:
                    pass

        build_dir = config_dir / "build"
        if build_dir.exists():
            shutil.rmtree(build_dir)
            print("  Cleaned: build/")

    finally:
        if setup_file.exists():
            setup_file.unlink()


def verify_build():
    """Verify the built native module loads and functions correctly."""
    config_dir = Path(__file__).parent.absolute()

    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))

    # Force reimport if already loaded
    if 'fee_native' in sys.modules:
        del sys.modules['fee_native']

    try:
        import fee_native

        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        fee = fee_native.get_fee_percentage()
        component = fee_native.get_fee_component_address()
        status = fee_native.get_security_status()

        print(f"  Fee percentage:    {fee}")
        print(f"  Component address: {component[:20]}...{component[-10:]}")
        print(f"  Integrity valid:   {status.get('integrity_valid', 'N/A')}")
        print(f"  Native module:     {status.get('native_module', False)}")
        print("\nNative module verified successfully.")
        return True

    except ImportError as e:
        print(f"ERROR: Could not import native module: {e}")
        print("  Ensure the module is built for this platform and Python version.")
        return False
    except Exception as e:
        print(f"ERROR: Module verification failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("RADBOT NATIVE MODULE BUILDER")
    print("=" * 60)
    print()

    if "--verify" in sys.argv:
        verify_build()
    else:
        build()
        print()
        verify_build()
