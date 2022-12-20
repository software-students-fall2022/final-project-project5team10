import gridfs
from werkzeug.utils import secure_filename
import codecs 

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename): # pragma: no cover
    '''
    check for allowed extensions
    '''
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def gridfs_helper_tool(db, grid_fs, reqFiles, book, currUser): # pragma: no cover
    if 'file' in reqFiles:  # check for allowed extensions
        file = reqFiles['file']
        if allowed_file((file.filename)):
            filename = secure_filename(file.filename)
            user = currUser
            # unique file name: user id + filename
            name = str(user.id) + "_" + str(filename)
            # upload file in chunks into the db using grid_fs
            id = grid_fs.put(file, filename=name)
            # document to be inserted into the images collection
            query = {
                "user": user.id,
                "book_name": book["title"],
                "img_id": id
            }
            # add gridfs id to the image field of the book document to be queried into the books collection
            book["image"] = id
            # get image chunks, read it, encode it, add the encoding to the "image_base64" field to be able to render it using html
            image = grid_fs.get(id)
            base64_data = codecs.encode(image.read(), 'base64')
            image = base64_data.decode('utf-8')
            book['image_base64'] = image
            # change the image_exists field to True once an image field is added to book document
            book['image_exists'] = True
            # add the image query into the images collection
            db.images.insert_one(query)
    db.books.insert_one(book)
