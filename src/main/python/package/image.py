import os

from PIL import Image


class CustomImage:
    """The CustomImage class implements the image reduction size and quality operation..

    Attributes:
        **image** *(Image)*: The image object from PIL.

        **width** *(int)*: The width of the image.

        **height** *(int)*: The height of the image.

        **path** *(str)*: The path of the image.

        **reduced_path** *(str)*: The path of the reduced image.
    """

    def __init__(self, path, folder="reduced"):
        """The constructor of the custom image object.

        :param path: The path of the image file.
        :param folder: The name of the output folder.
        :type path: str
        :type folder: str
        """
        self.image = Image.open(path)
        self.width, self.height = self.image.size
        self.path = path
        self.reduced_path = os.path.join(os.path.dirname(self.path),
                                         folder,
                                         os.path.basename(self.path))

    def reduce_image(self, size=0.5, quality=75):
        """Set the size and the quality of the image.

        :param size: The reduction size coefficient.
        :param quality: The percentage of quality.
        :type size: float
        :type quality: int

        :return: True if the path of the reduced image exists else False.
        :rtype: bool
        """
        new_width = round(self.width * size)
        new_height = round(self.height * size)
        self.image = self.image.resize((new_width, new_height), Image.ANTIALIAS)
        parent_dir = os.path.dirname(self.reduced_path)

        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        self.image.save(self.reduced_path, 'JPEG', quality=quality)
        return os.path.exists(self.reduced_path)
