1. Setup and environment
# ensure you're inside your venv
.venv\Scripts\activate

# make sure your build toolchain and cython are installed
pip install --upgrade pip setuptools wheel build cython twine

2. Clean previous outputs
# remove any old build artifacts
Remove-Item -Recurse -Force build, dist, src\ornata\optimization\cython\*.c, src\ornata\optimization\cython\*.pyd

3. Compile your .pyx → .c → .pyd
# generate C files from .pyx
python -m cython src\ornata\optimization\cython\vdom_diff.pyx

# compile .c into .pyd binaries
python setup.py build_ext --inplace


After this step you should see .pyd files like:

src\ornata\optimization\cython\vdom_diff.cp314-win_amd64.pyd
...

4. Build final PyPI distributions
# build both wheels (normal + free-threaded) and source distribution
python -m build --wheel --sdist --no-isolation


Output in dist\:

ornata-0.7.0-cp314-cp314-win_amd64.whl
ornata-0.7.0-cp314-cp314t-win_amd64.whl
ornata-0.7.0.tar.gz

5. Verify your builds
python -m twine check dist\*


Should show:

Checking dist\ornata-0.7.0-...
PASSED

6. Upload to TestPyPI first (optional but recommended)
python -m twine upload --repository testpypi dist\*


Visit:
🔗 https://test.pypi.org/project/ornata/

7. Upload to the real PyPI
python -m twine upload dist\*


Then check:
https://pypi.org/project/ornata/

Summary of the full sequence
.venv\Scripts\activate
pip install --upgrade pip setuptools wheel build cython twine
Remove-Item -Recurse -Force build, dist, src\ornata\optimization\cython\*.c, src\ornata\optimization\cython\*.pyd
python -m cython src\ornata\optimization\cython\color_ops.pyx
python -m cython src\ornata\optimization\cython\diffing_ops.pyx
python -m cython src\ornata\optimization\cython\layout_ops.pyx
python -m cython src\ornata\optimization\cython\rendering_ops.pyx
python -m cython src\ornata\optimization\cython\text_ops.pyx
python setup.py build_ext --inplace
python -m build --wheel --sdist --no-isolation
python -m twine check dist\*
python -m twine upload --repository testpypi dist\*
# (after verifying)
python -m twine upload dist\*

# Full Build Chain:

uv pip uninstall dist/ornata-0.7.0-cp314-cp314-win_amd64.whl
Remove-Item -Recurse -Force build, dist, src\ornata\optimization\cython\*.c, src\ornata\optimization\cython\*.pyd
python -m cython src\ornata\optimization\cython\vdom_diff.pyx
python setup.py build_ext --inplace
python -m build --wheel --sdist --no-isolation
python -m twine check dist\*
uv pip install dist/ornata-0.7.0-cp314-cp314-win_amd64.whl



# Optional, run benchmarks
uv run --active benchmark.py
