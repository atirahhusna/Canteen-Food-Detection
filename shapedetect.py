import cv2
import numpy as np

def detect_shape(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    output = img.copy()

    #use cannyline
    blurred_image = cv2.GaussianBlur(gray, (5, 5), 1.4)
    edges = cv2.Canny(blurred_image, 255, 255)
    

    # cv2.imshow("Result", edges)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No contours found.")
        exit()

    # Sort contours by area in descending order
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

    if len(sorted_contours) >= 2:
        largest_contour = sorted_contours[0]
        second_largest_contour = sorted_contours[1]
        combined_contour = np.vstack((largest_contour, second_largest_contour))
    else:
        combined_contour = sorted_contours[0]

    epsilon = 0.01 * cv2.arcLength(combined_contour, True)
    approx = cv2.approxPolyDP(combined_contour, epsilon, True)

     # vis2 = img.copy()
    # cv2.drawContours(vis2, [approx], -1, (255, 0, 0), 2)  # blue simplified outline
    # for i, (x, y) in enumerate(approx.reshape(-1, 2)):
    #     cv2.circle(vis2, (x, y), 3, (0, 165, 255), -1)   # orange vertices
    #     cv2.putText(vis2, str(i), (x + 3, y - 3),
    #                 cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

    # cv2.imshow("Result", vis2)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows() 

    num_vertices = len(approx)

    if num_vertices >= 7:
        # Likely round → apply fitEllipse
        ellipse = cv2.fitEllipse(approx)
        (center, axes, angle) = ellipse
        major_axis = max(axes)
        minor_axis = min(axes)

        # Eccentricity calculation
        eccentricity = np.sqrt(1 - (minor_axis**2 / major_axis**2))

        eccentricity_threshold = 0.6
        axis_ratio = major_axis / minor_axis if minor_axis != 0 else 1

        if eccentricity < eccentricity_threshold or axis_ratio < 1.15:
            shape = "circle"
        else:
            shape = "oval"

        print(f"Shape: {shape}")
        print(f"  Eccentricity: {eccentricity:.3f}")
        print(f"  Major axis: {major_axis:.2f}px")
        print(f"  Minor axis: {minor_axis:.2f}px")

        # # Draw ellipse on image
        # out = img.copy()
        # cv2.ellipse(out, ellipse, (0, 255, 0), 2)
        # cv2.imshow("Result", out)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

   
    return shape

    