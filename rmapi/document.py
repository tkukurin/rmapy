from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED
import shutil
from uuid import uuid4
import json
from typing import NoReturn, TypeVar
from requests import Response

BytesOrString = TypeVar("BytesOrString", BytesIO, str)


class Document(object):
    """ Document represents a real object expected in most
    calls by the remarkable API

    This contains the metadata from a document.

    Attributes:
        ID: Id of the meta object.
        Version: The version of this object.
        Success: If the last API Call was a succes.
        BlobURLGet: The url to get the data blob from. Can be empty.
        BlobURLGetExpires: The expiration date of the Get url.
        BlobURLPut: The url to upload the data blob to. Can be empty.
        BlobURLPutExpires: The expiration date of the Put url.
        ModifiedClient: When the last change was by the client.
        Type: Currently there are only 2 known types: DocumentType &
            CollectionType.
        VissibleName: The human name of the object.
        CurrentPage: The current selected page of the object.
        Bookmarked: If the object is bookmarked.
        Parent: If empty, this object is is the root folder. This can be an ID
            of a CollectionType.

    """

    ID = ""
    Version = 0
    Message = ""
    Succes = True
    BlobURLGet = ""
    BlobURLGetExpires = ""
    BlobURLPut = ""
    BlobURLPutExpires = ""
    ModifiedClient = ""
    Type = "DocumentType"
    VissibleName = ""
    CurrentPage = 1
    Bookmarked = False
    Parent = ""

    def __init__(self, **kwargs):
        kkeys = self.to_dict().keys()
        for k in kkeys:
            setattr(self, k, kwargs.get(k, getattr(self, k)))

    def to_dict(self) -> dict:
        """Return a dict representation of this object.

        Used for API Calls.

        Returns
            a dict of the current object.
        """

        return {
            "ID": self.ID,
            "Version": self.Version,
            "Message": self.Message,
            "Succes": self.Succes,
            "BlobURLGet": self.BlobURLGet,
            "BlobURLGetExpires": self.BlobURLGetExpires,
            "BlobURLPut": self.BlobURLPut,
            "BlobURLPutExpires": self.BlobURLPutExpires,
            "ModifiedClient": self.ModifiedClient,
            "Type": self.Type,
            "VissibleName": self.VissibleName,
            "CurrentPage": self.CurrentPage,
            "Bookmarked": self.Bookmarked,
            "Parent": self.Parent
        }

    def __str__(self):
        """String representation of this object"""
        return f"<rmapi.document.Document {self.ID}>"

    def __repr__(self):
        """String representation of this object"""
        return self.__str__()


class ZipDocument(object):
    """
    Here is the content of an archive retried on the tablet as example:

    * 384327f5-133e-49c8-82ff-30aa19f3cfa40.content
    * 384327f5-133e-49c8-82ff-30aa19f3cfa40-metadata.json
    * 384326f5-133e-49c8-82ff-30aa19f3cfa40.rm
    * 384327f5-133e-49c8-82ff-30aa19f3cfa40.pagedata
    * 384327f5-133e-49c8-82ff-30aa19f3cfa40.thumbnails/0.jpg

    As the .zip file from remarkable is simply a normal .zip file
    containing specific file formats, this package is a helper to
    read and write zip files with the correct format expected by
    the tablet.

    In order to correctly use this package, you will have to understand
    the format of a Remarkable zip file, and the format of the files
    that it contains.

    You can find some help about the format at the following URL:
    https://remarkablewiki.com/tech/filesystem

    Attributes:
        content: Sane defaults for the .content file in the zip.
        metadata: parameters describing this blob.
        pagedata: the content of the .pagedata file.
        zipfile: The raw zipfile in memory.
        pdf: the raw pdf file if there is one.
        epub: the raw epub file if there is one.
        rm: A list of :class:rmapi.document.RmPage in this zip.

    """
    content = {
        "ExtraMetadata": {
            "LastBrushColor": "Black",
            "LastBrushThicknessScale": "2",
            "LastColor": "Black",
            "LastEraserThicknessScale": "2",
            "LastEraserTool": "Eraser",
            "LastPen": "Ballpoint",
            "LastPenColor": "Black",
            "LastPenThicknessScale": "2",
            "LastPencil": "SharpPencil",
            "LastPencilColor": "Black",
            "LastPencilThicknessScale": "2",
            "LastTool": "SharpPencil",
            "ThicknessScale": "2"
        },
        "FileType": "",
        "FontName": "",
        "LastOpenedPage": 0,
        "LineHeight": -1,
        "Margins": 100,
        "Orientation": "portrait",
        "PageCount": 0,
        "Pages": [],
        "TextScale": 1,
        "Transform": {
            "M11": 1,
            "M12": 0,
            "M13": 0,
            "M21": 0,
            "M22": 1,
            "M23": 0,
            "M31": 0,
            "M32": 0,
            "M33": 1,
        }
    }

    metadata = {
        "deleted": False,
        "lastModified": "1568368808000",
        "metadatamodified": False,
        "modified": False,
        "parent": "",
        "pinned": False,
        "synced": True,
        "type": "DocumentType",
        "version": 1,
        "visibleName": "New Document"
    }

    pagedata = ""

    zipfile = BytesIO()
    pdf = None
    epub = None
    rm = []
    ID = None

    def __init__(self, ID=None, doc=None, file=None):
        """Create a new instance of a ZipDocument

        Args:
            ID: Can be left empty to generate one
            doc: a raw pdf, epub or rm (.lines) file.
            file: a zipfile to convert from
        """
        if not ID:
            ID = str(uuid4())
        self.ID = ID
        if doc:
            ext = doc[-4:]
            if ext.endswith("pdf"):
                self.content["FileType"] = "pdf"
                self.pdf = BytesIO()
                with open(doc, 'rb') as fb:
                    self.pdf.write(fb.read())
            if ext.endswith("epub"):
                self.content["FileType"] = "epub"
                self.epub = BytesIO()
                with open(doc, 'rb') as fb:
                    self.epub.write(fb.read())
            elif ext.endswith("rm"):
                self.content["FileType"] = "notebook"
                self.pdf = BytesIO()
                with open(doc, 'rb') as fb:
                    self.rm.append(RmPage(page=BytesIO(doc.read())))

        if file:
            self.load(file)

    def __str__(self) -> str:
        """string representation of this class"""
        return f"<rmapi.document.ZipDocument {self.ID}>"

    def __repr__(self) -> str:
        """string representation of this class"""
        return self.__str__()

    def dump(self, file: str) -> NoReturn:
        """Dump the contents of ZipDocument back to a zip file.

        This builds a zipfile to upload back to the Remarkable Cloud.

        Args:
            file: Where to save the zipfile

        """

        with ZipFile(f"{file}.zip", "w", ZIP_DEFLATED) as zf:
            if self.content:
                zf.writestr(f"{self.ID}.content",
                            json.dumps(self.content))
            if self.pagedata:
                zf.writestr(f"{self.ID}.pagedata",
                            self.pagedata.read())

            if self.pdf:
                zf.writestr(f"{self.ID}.pdf",
                            self.pdf.read())

            if self.epub:
                zf.writestr(f"{self.ID}.epub",
                            self.epub.read())

            for page in self.rm:

                zf.writestr(f"{self.ID}/{page.order}.rm",
                            page.page.read())

                zf.writestr(f"{self.ID}/{page.order}-metadata.json",
                            json.dumps(page.metadata))
                page.page.seek(0)
                zf.writestr(f"{self.ID}.thumbnails/{page.order}.jpg",
                            page.thumbnail.read())

    def load(self, file: BytesOrString) -> NoReturn:
        """Load a zipfile into this class.

        Extracts the zipfile and reads in the contents.

        Args:
            file: A string of a file location or a BytesIO instance of a raw
                zipfile
        """

        self.zipfile = BytesIO()
        self.zipfile.seek(0)
        if isinstance(file, str):
            with open(file, 'rb') as f:
                shutil.copyfileobj(f, self.zipfile)
        elif isinstance(file, BytesIO):
            self.zipfile = file
            self.zipfile.seek(0)
        else:
            raise Exception("Unsupported file type.")
        with ZipFile(self.zipfile, 'r') as zf:
            with zf.open(f"{self.ID}.content", 'r') as content:
                self.content = json.load(content)
            try:
                with zf.open(f"{self.ID}.metadata", 'r') as metadata:
                    self.metadata = json.load(metadata)
            except KeyError:
                pass
            try:
                with zf.open(f"{self.ID}.pagedata", 'r') as pagedata:
                    self.pagedata = BytesIO(pagedata.read())
            except KeyError:
                pass

            try:
                with zf.open(f"{self.ID}.pdf", 'r') as pdf:
                    self.pdf = BytesIO(pdf.read())
            except KeyError:
                pass

            try:
                with zf.open(f"{self.ID}.epub", 'r') as epub:
                    self.epub = BytesIO(epub.read())
            except KeyError:
                pass

            # Get the RM pages

            content = [x for x in zf.namelist()
                       if x.startswith(f"{self.ID}/") and x.endswith('.rm')]
            for p in content:
                pagenumber = p.replace(f"{self.ID}/", "").replace(".rm", "")
                pagenumber = int(pagenumber)
                page = BytesIO()
                thumbnail = BytesIO()
                with zf.open(p, 'r') as rm:
                    page = BytesIO(rm.read())
                    page.seek(0)
                with zf.open(p.replace(".rm", "-metadata.json"), 'r') as md:
                    metadata = json.load(md)
                thumbnail_name = p.replace(".rm", ".jpg")
                thumbnail_name = thumbnail_name.replace("/", ".thumbnails/")
                with zf.open(thumbnail_name, 'r') as tn:
                    thumbnail = BytesIO(tn.read())
                    thumbnail.seek(0)

                self.rm.append(RmPage(page, metadata, pagenumber, thumbnail,
                                      self.ID))

        self.zipfile.seek(0)


class RmPage(object):
    """A Remarkable Page

    Contains the metadata, the page itself & thumbnail.

    """
    def __init__(self, page, metadata=None, order=0, thumbnail=None, ID=None):
        self.page = page
        if metadata:
            self.metadata = metadata
        else:
            self.metadata = {"layers": [{"name": "Layer 1"}]}

        self.order = order
        if thumbnail:
            self.thumbnail = thumbnail
        if ID:
            self.ID = ID
        else:
            self.ID = str(uuid4())

    def __str__(self) -> str:
        """String representation of this object"""
        return f"<rmapi.document.RmPage {self.order} for {self.ID}>"

    def __repr__(self) -> str:
        """String representation of this object"""
        return self.__str__()


def from_zip(ID: str, file: str) -> ZipDocument:
    """Return A ZipDocument from a zipfile.

    Create a ZipDocument instance from a zipfile.

    Args:
        ID: The object ID this zipfile represents.
        file: the filename of the zipfile.
    Returns:
        An instance of the supplied zipfile.
    """

    return ZipDocument(ID, file=file)


def from_request_stream(ID: str, stream:  Response) -> ZipDocument:
    """Return a ZipDocument from a request stream containing a zipfile.

    This is used with the BlobGETUrl from a :class:`rmapi.document.Document`.

    Args:
        ID: The object ID this zipfile represents.
        stream: a stream containing the zipfile.
    Returns:
        the object of the downloaded zipfile.
    """

    tmp = BytesIO()
    for chunk in stream.iter_content(chunk_size=8192):
        tmp.write(chunk)
    zd = ZipDocument(ID=ID)
    zd.load(tmp)
    return zd
