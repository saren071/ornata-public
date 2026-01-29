"""Software math operations for matrices, vectors, and transformations."""

import math

from ornata.api.exports.definitions import Matrix4, Vector2, Vector3


def identity_matrix() -> Matrix4:
    """Create an identity matrix.

    Returns:
        Matrix4: A 4x4 identity matrix.
    """
    return Matrix4([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def matrix_multiply(a: Matrix4, b: Matrix4) -> Matrix4:
    """Multiply two 4x4 matrices.

    Args:
        a: First matrix.
        b: Second matrix.

    Returns:
        Matrix4: Result of a * b.
    """
    result = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            for k in range(4):
                result[i][j] += a.data[i][k] * b.data[k][j]
    return Matrix4(result)


def vector_add(a: Vector3, b: Vector3) -> Vector3:
    """Add two 3D vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Vector3: Sum of the vectors.
    """
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vector_subtract(a: Vector3, b: Vector3) -> Vector3:
    """Subtract two 3D vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Vector3: Difference of the vectors.
    """
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vector_scale(v: Vector3, s: float) -> Vector3:
    """Scale a 3D vector by a scalar.

    Args:
        v: Vector to scale.
        s: Scale factor.

    Returns:
        Vector3: Scaled vector.
    """
    return (v[0] * s, v[1] * s, v[2] * s)


def vector_dot(a: Vector3, b: Vector3) -> float:
    """Compute dot product of two 3D vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        float: Dot product.
    """
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vector_cross(a: Vector3, b: Vector3) -> Vector3:
    """Compute cross product of two 3D vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        Vector3: Cross product.
    """
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0]
    )


def vector_length(v: Vector3) -> float:
    """Compute length of a 3D vector.

    Args:
        v: Vector.

    Returns:
        float: Length of the vector.
    """
    return math.sqrt(vector_dot(v, v))


def vector_normalize(v: Vector3) -> Vector3:
    """Normalize a 3D vector.

    Args:
        v: Vector to normalize.

    Returns:
        Vector3: Normalized vector.

    Raises:
        ValueError: If vector length is zero.
    """
    length = vector_length(v)
    if length == 0.0:
        raise ValueError("Cannot normalize zero-length vector")
    return vector_scale(v, 1.0 / length)


def transform_point(matrix: Matrix4, point: Vector3) -> Vector3:
    """Transform a 3D point using a 4x4 matrix.

    Args:
        matrix: Transformation matrix.
        point: Point to transform.

    Returns:
        Vector3: Transformed point.
    """
    x, y, z = point
    w = 1.0
    tx = matrix.data[0][0] * x + matrix.data[0][1] * y + matrix.data[0][2] * z + matrix.data[0][3] * w
    ty = matrix.data[1][0] * x + matrix.data[1][1] * y + matrix.data[1][2] * z + matrix.data[1][3] * w
    tz = matrix.data[2][0] * x + matrix.data[2][1] * y + matrix.data[2][2] * z + matrix.data[2][3] * w
    tw = matrix.data[3][0] * x + matrix.data[3][1] * y + matrix.data[3][2] * z + matrix.data[3][3] * w

    if tw != 0.0:
        tx /= tw
        ty /= tw
        tz /= tw

    return (tx, ty, tz)


def transform_vector(matrix: Matrix4, vector: Vector3) -> Vector3:
    """Transform a 3D vector using a 4x4 matrix (no translation).

    Args:
        matrix: Transformation matrix.
        vector: Vector to transform.

    Returns:
        Vector3: Transformed vector.
    """
    x, y, z = vector
    tx = matrix.data[0][0] * x + matrix.data[0][1] * y + matrix.data[0][2] * z
    ty = matrix.data[1][0] * x + matrix.data[1][1] * y + matrix.data[1][2] * z
    tz = matrix.data[2][0] * x + matrix.data[2][1] * y + matrix.data[2][2] * z

    return (tx, ty, tz)


def translate_matrix(tx: float, ty: float, tz: float) -> Matrix4:
    """Create a translation matrix.

    Args:
        tx: Translation in x.
        ty: Translation in y.
        tz: Translation in z.

    Returns:
        Matrix4: Translation matrix.
    """
    return Matrix4([
        [1.0, 0.0, 0.0, tx],
        [0.0, 1.0, 0.0, ty],
        [0.0, 0.0, 1.0, tz],
        [0.0, 0.0, 0.0, 1.0]
    ])


def scale_matrix(sx: float, sy: float, sz: float) -> Matrix4:
    """Create a scaling matrix.

    Args:
        sx: Scale in x.
        sy: Scale in y.
        sz: Scale in z.

    Returns:
        Matrix4: Scaling matrix.
    """
    return Matrix4([
        [sx, 0.0, 0.0, 0.0],
        [0.0, sy, 0.0, 0.0],
        [0.0, 0.0, sz, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def rotate_x_matrix(angle: float) -> Matrix4:
    """Create a rotation matrix around x-axis.

    Args:
        angle: Rotation angle in radians.

    Returns:
        Matrix4: Rotation matrix.
    """
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix4([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, c, -s, 0.0],
        [0.0, s, c, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def rotate_y_matrix(angle: float) -> Matrix4:
    """Create a rotation matrix around y-axis.

    Args:
        angle: Rotation angle in radians.

    Returns:
        Matrix4: Rotation matrix.
    """
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix4([
        [c, 0.0, s, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [-s, 0.0, c, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def rotate_z_matrix(angle: float) -> Matrix4:
    """Create a rotation matrix around z-axis.

    Args:
        angle: Rotation angle in radians.

    Returns:
        Matrix4: Rotation matrix.
    """
    c = math.cos(angle)
    s = math.sin(angle)
    return Matrix4([
        [c, -s, 0.0, 0.0],
        [s, c, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def look_at_matrix(eye: Vector3, target: Vector3, up: Vector3) -> Matrix4:
    """Create a view matrix using look-at parameters.

    Args:
        eye: Camera position.
        target: Target position.
        up: Up vector.

    Returns:
        Matrix4: View matrix.
    """
    forward = vector_normalize(vector_subtract(target, eye))
    right = vector_normalize(vector_cross(forward, up))
    up_new = vector_cross(right, forward)

    return Matrix4([
        [right[0], up_new[0], -forward[0], 0.0],
        [right[1], up_new[1], -forward[1], 0.0],
        [right[2], up_new[2], -forward[2], 0.0],
        [-vector_dot(right, eye), -vector_dot(up_new, eye), vector_dot(forward, eye), 1.0]
    ])


def perspective_matrix(fov: float, aspect: float, near: float, far: float) -> Matrix4:
    """Create a perspective projection matrix.

    Args:
        fov: Field of view in radians.
        aspect: Aspect ratio (width/height).
        near: Near clipping plane.
        far: Far clipping plane.

    Returns:
        Matrix4: Perspective projection matrix.
    """
    f = 1.0 / math.tan(fov / 2.0)
    return Matrix4([
        [f / aspect, 0.0, 0.0, 0.0],
        [0.0, f, 0.0, 0.0],
        [0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far)],
        [0.0, 0.0, -1.0, 0.0]
    ])


def orthographic_matrix(left: float, right: float, bottom: float, top: float, near: float, far: float) -> Matrix4:
    """Create an orthographic projection matrix.

    Args:
        left: Left clipping plane.
        right: Right clipping plane.
        bottom: Bottom clipping plane.
        top: Top clipping plane.
        near: Near clipping plane.
        far: Far clipping plane.

    Returns:
        Matrix4: Orthographic projection matrix.
    """
    return Matrix4([
        [2.0 / (right - left), 0.0, 0.0, -(right + left) / (right - left)],
        [0.0, 2.0 / (top - bottom), 0.0, -(top + bottom) / (top - bottom)],
        [0.0, 0.0, -2.0 / (far - near), -(far + near) / (far - near)],
        [0.0, 0.0, 0.0, 1.0]
    ])


def viewport_matrix(x: float, y: float, width: float, height: float) -> Matrix4:
    """Create a viewport transformation matrix.

    Args:
        x: Viewport x offset.
        y: Viewport y offset.
        width: Viewport width.
        height: Viewport height.

    Returns:
        Matrix4: Viewport matrix.
    """
    return Matrix4([
        [width / 2.0, 0.0, 0.0, x + width / 2.0],
        [0.0, height / 2.0, 0.0, y + height / 2.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
    ])


def ndc_to_screen(ndc: Vector3, viewport_x: float, viewport_y: float, viewport_width: float, viewport_height: float) -> Vector2:
    """Convert NDC coordinates to screen coordinates.

    Args:
        ndc: NDC coordinates (x, y, z).
        viewport_x: Viewport x offset.
        viewport_y: Viewport y offset.
        viewport_width: Viewport width.
        viewport_height: Viewport height.

    Returns:
        Vector2: Screen coordinates.
    """
    screen_x = (ndc[0] + 1.0) * viewport_width / 2.0 + viewport_x
    screen_y = (1.0 - ndc[1]) * viewport_height / 2.0 + viewport_y
    return (screen_x, screen_y)


def screen_to_ndc(screen: Vector2, viewport_x: float, viewport_y: float, viewport_width: float, viewport_height: float) -> Vector3:
    """Convert screen coordinates to NDC coordinates.

    Args:
        screen: Screen coordinates (x, y).
        viewport_x: Viewport x offset.
        viewport_y: Viewport y offset.
        viewport_width: Viewport width.
        viewport_height: Viewport height.

    Returns:
        Vector3: NDC coordinates (x, y, 0).
    """
    ndc_x = 2.0 * (screen[0] - viewport_x) / viewport_width - 1.0
    ndc_y = 1.0 - 2.0 * (screen[1] - viewport_y) / viewport_height
    return (ndc_x, ndc_y, 0.0)