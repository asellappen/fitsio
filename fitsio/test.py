from __future__ import with_statement, print_function
import sys, os
import tempfile
import warnings
import numpy
from numpy import arange, array
import fitsio

from ._fitsio_wrap import cfitsio_use_standard_strings

import unittest

try:
    xrange=xrange
except:
    xrange=range

lorem_ipsum = (
    'Lorem ipsum dolor sit amet, consectetur adipiscing '
    'elit, sed do eiusmod tempor incididunt ut labore '
    'et dolore magna aliqua'
)
def test():
    suite_warnings = unittest.TestLoader().loadTestsFromTestCase(TestWarnings)
    res1=unittest.TextTestRunner(verbosity=2).run(suite_warnings).wasSuccessful()

    suite = unittest.TestLoader().loadTestsFromTestCase(TestReadWrite)
    res2=unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()

    if not res1 or not res2:
        sys.exit(1)

class TestWarnings(unittest.TestCase):
    """
    tests of warnings

    TODO: write test cases for bad column size
    """
    def setUp(self):
        pass

    def testNonStandardKeyValue(self):
        fname=tempfile.mktemp(prefix='fitsio-TestWarning-',suffix='.fits')

        im=numpy.zeros( (3,3) )
        with warnings.catch_warnings(record=True) as w:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write(im)
                # now write a key with a non-standard value
                value={'test':3}
                fits[-1].write_key("odd",value)

            assert len(w) == 1
            assert issubclass(w[-1].category, fitsio.FITSRuntimeWarning)

class TestReadWrite(unittest.TestCase):

    def setUp(self):

        nvec = 2
        ashape=(21,21)
        Sdtype = 'S6'
        Udtype = 'U6'

        # all currently available types, scalar, 1-d and 2-d array columns
        dtype=[
            ('u1scalar','u1'),
            ('i1scalar','i1'),
            ('b1scalar','?'),
            ('u2scalar','u2'),
            ('i2scalar','i2'),
            ('u4scalar','u4'),
            ('i4scalar','<i4'), # mix the byte orders a bit, test swapping
            ('i8scalar','i8'),
            ('f4scalar','f4'),
            ('f8scalar','>f8'),
            ('c8scalar','c8'), # complex, two 32-bit
            ('c16scalar','c16'), # complex, two 32-bit

            ('u1vec','u1',nvec),
            ('i1vec','i1',nvec),
            ('b1vec','?',nvec),
            ('u2vec','u2',nvec),
            ('i2vec','i2',nvec),
            ('u4vec','u4',nvec),
            ('i4vec','i4',nvec),
            ('i8vec','i8',nvec),
            ('f4vec','f4',nvec),
            ('f8vec','f8',nvec),
            ('c8vec','c8',nvec),
            ('c16vec','c16',nvec),

            ('u1arr','u1',ashape),
            ('i1arr','i1',ashape),
            ('b1arr','?',ashape),
            ('u2arr','u2',ashape),
            ('i2arr','i2',ashape),
            ('u4arr','u4',ashape),
            ('i4arr','i4',ashape),
            ('i8arr','i8',ashape),
            ('f4arr','f4',ashape),
            ('f8arr','f8',ashape),
            ('c8arr','c8',ashape),
            ('c16arr','c16',ashape),

            # special case of (1,)
            ('f8arr_dim1','f8',(1,)),


            ('Sscalar',Sdtype),
            ('Svec',   Sdtype, nvec),
            ('Sarr',   Sdtype, ashape),
        ]

        if cfitsio_use_standard_strings():
            dtype += [
                ('Sscalar_nopad',Sdtype),
                ('Svec_nopad',   Sdtype, nvec),
                ('Sarr_nopad',   Sdtype, ashape),
            ]

        if sys.version_info > (3,0,0):
            dtype += [
               ('Uscalar',Udtype),
               ('Uvec',   Udtype, nvec),
               ('Uarr',   Udtype, ashape),
            ]

            if cfitsio_use_standard_strings():
                dtype += [
                   ('Uscalar_nopad',Udtype),
                   ('Uvec_nopad',   Udtype, nvec),
                   ('Uarr_nopad',   Udtype, ashape),
                ]


        dtype2=[('index','i4'),
                ('x','f8'),
                ('y','f8')]

        nrows=4
        data=numpy.zeros(nrows, dtype=dtype)

        dtypes=['u1','i1','u2','i2','u4','i4','i8','f4','f8','c8','c16']
        for t in dtypes:
            if t in ['c8','c16']:
                data[t+'scalar'] = [complex(i+1,(i+1)*2) for i in xrange(nrows)]
                vname=t+'vec'
                for row in xrange(nrows):
                    for i in xrange(nvec):
                        index=(row+1)*(i+1)
                        data[vname][row,i] = complex(index,index*2)
                aname=t+'arr'
                for row in xrange(nrows):
                    for i in xrange(ashape[0]):
                        for j in xrange(ashape[1]):
                            index=(row+1)*(i+1)*(j+1)
                            data[aname][row,i,j] = complex(index,index*2)

            else:
                data[t+'scalar'] = 1 + numpy.arange(nrows, dtype=t)
                data[t+'vec'] = 1 + numpy.arange(nrows*nvec,dtype=t).reshape(nrows,nvec)
                arr = 1 + numpy.arange(nrows*ashape[0]*ashape[1],dtype=t)
                data[t+'arr'] = arr.reshape(nrows,ashape[0],ashape[1])

        for t in ['b1']:
            data[t+'scalar'] = (numpy.arange(nrows) % 2 == 0).astype('?')
            data[t+'vec'] = (numpy.arange(nrows*nvec) % 2 == 0).astype('?').reshape(nrows,nvec)
            arr = (numpy.arange(nrows*ashape[0]*ashape[1]) % 2 == 0).astype('?')
            data[t+'arr'] = arr.reshape(nrows,ashape[0],ashape[1])


        # strings get padded when written to the fits file.  And the way I do
        # the read, I read all bytes (ala mrdfits) so the spaces are preserved.
        #
        # so we need to pad out the strings with blanks so we can compare

        data['Sscalar'] = ['%-6s' % s for s in ['hello','world','good','bye']]
        data['Svec'][:,0] = '%-6s' % 'hello'
        data['Svec'][:,1] = '%-6s' % 'world'


        s = 1 + numpy.arange(nrows*ashape[0]*ashape[1])
        s = ['%-6s' % el for el in s]
        data['Sarr'] = numpy.array(s).reshape(nrows,ashape[0],ashape[1])

        if cfitsio_use_standard_strings():
            data['Sscalar_nopad'] = ['hello','world','good','bye']
            data['Svec_nopad'][:,0] = 'hello'
            data['Svec_nopad'][:,1] = 'world'

            s = 1 + numpy.arange(nrows*ashape[0]*ashape[1])
            s = ['%s' % el for el in s]
            data['Sarr_nopad'] = numpy.array(s).reshape(nrows,ashape[0],ashape[1])

        if sys.version_info >= (3, 0, 0):
            data['Uscalar'] = ['%-6s' % s for s in ['hello','world','good','bye']]
            data['Uvec'][:,0] = '%-6s' % 'hello'
            data['Uvec'][:,1] = '%-6s' % 'world'

            s = 1 + numpy.arange(nrows*ashape[0]*ashape[1])
            s = ['%-6s' % el for el in s]
            data['Uarr'] = numpy.array(s).reshape(nrows,ashape[0],ashape[1])


            if cfitsio_use_standard_strings():
                data['Uscalar_nopad'] = ['hello','world','good','bye']
                data['Uvec_nopad'][:,0] = 'hello'
                data['Uvec_nopad'][:,1] = 'world'

                s = 1 + numpy.arange(nrows*ashape[0]*ashape[1])
                s = ['%s' % el for el in s]
                data['Uarr_nopad'] = numpy.array(s).reshape(nrows,ashape[0],ashape[1])

        self.data = data

        # use a dict list so we can have comments
        self.keys = [{'name':'test1','value':35},
                     {'name':'empty','value':''},
                     {'name':'test2','value':'stuff','comment':'this is a string keyword'},
                     {'name':'dbl', 'value':23.299843,'comment':"this is a double keyword"},
                     {'name':'lng','value':3423432,'comment':'this is a long keyword'},
                     {'name':'lngstr','value':lorem_ipsum,'comment':'long string'}]

        # a second extension using the convenience function
        nrows2=10
        data2 = numpy.zeros(nrows2, dtype=dtype2)
        data2['index'] = numpy.arange(nrows2,dtype='i4')
        data2['x'] = numpy.arange(nrows2,dtype='f8')
        data2['y'] = numpy.arange(nrows2,dtype='f8')
        self.data2 = data2

        #
        # ascii table
        #

        nvec = 2
        ashape = (2,3)
        Sdtype = 'S6'
        Udtype = 'U6'

        # we support writing i2, i4, i8, f4 f8, but when reading cfitsio always
        # reports their types as i4 and f8, so can't really use i8 and we are
        # forced to read all floats as f8 precision

        adtype=[('i2scalar','i2'),
                ('i4scalar','i4'),
                #('i8scalar','i8'),
                ('f4scalar','f4'),
                ('f8scalar','f8'),
                ('Sscalar',Sdtype)]
        if sys.version_info >= (3, 0, 0):
            adtype += [('Uscalar', Udtype)]

        nrows=4
        try:
            tdt = numpy.dtype(adtype, align=True)
        except TypeError: # older numpy may not understand `align` argument
            tdt = numpy.dtype(adtype)
        adata=numpy.zeros(nrows, dtype=tdt)

        adata['i2scalar'][:] = -32222  + numpy.arange(nrows,dtype='i2')
        adata['i4scalar'][:] = -1353423423 + numpy.arange(nrows,dtype='i4')
        #adata['i8scalar'][:] = -9223372036854775807 + numpy.arange(nrows,dtype='i8')
        adata['f4scalar'][:] = -2.55555555555555555555555e35 + numpy.arange(nrows,dtype='f4')*1.e35
        adata['f8scalar'][:] = -2.55555555555555555555555e110 + numpy.arange(nrows,dtype='f8')*1.e110
        adata['Sscalar'] = ['hello','world','good','bye']

        if sys.version_info >= (3, 0, 0):
            adata['Uscalar'] = ['hello','world','good','bye']

        self.ascii_data = adata



        #
        # for variable length columns
        #

        # all currently available types, scalar, 1-d and 2-d array columns
        dtype=[
            ('u1scalar','u1'),
            ('u1obj','O'),
            ('i1scalar','i1'),
            ('i1obj','O'),
            ('u2scalar','u2'),
            ('u2obj','O'),
            ('i2scalar','i2'),
            ('i2obj','O'),
            ('u4scalar','u4'),
            ('u4obj','O'),
            ('i4scalar','<i4'), # mix the byte orders a bit, test swapping
            ('i4obj','O'),
            ('i8scalar','i8'),
            ('i8obj','O'),
            ('f4scalar','f4'),
            ('f4obj','O'),
            ('f8scalar','>f8'),
            ('f8obj','O'),

            ('u1vec','u1',nvec),
            ('i1vec','i1',nvec),
            ('u2vec','u2',nvec),
            ('i2vec','i2',nvec),
            ('u4vec','u4',nvec),
            ('i4vec','i4',nvec),
            ('i8vec','i8',nvec),
            ('f4vec','f4',nvec),
            ('f8vec','f8',nvec),

            ('u1arr','u1',ashape),
            ('i1arr','i1',ashape),
            ('u2arr','u2',ashape),
            ('i2arr','i2',ashape),
            ('u4arr','u4',ashape),
            ('i4arr','i4',ashape),
            ('i8arr','i8',ashape),
            ('f4arr','f4',ashape),
            ('f8arr','f8',ashape),

            # special case of (1,)
            ('f8arr_dim1','f8',(1,)),

            ('Sscalar',Sdtype),
            ('Sobj','O'),
            ('Svec',   Sdtype, nvec),
            ('Sarr',   Sdtype, ashape),
        ]

        if sys.version_info > (3,0,0):
            dtype += [
               ('Uscalar',Udtype),
               ('Uvec',   Udtype, nvec),
               ('Uarr',   Udtype, ashape)]

        dtype2=[('index','i4'),
                ('x','f8'),
                ('y','f8')]

        nrows=4
        data=numpy.zeros(nrows, dtype=dtype)

        for t in ['u1','i1','u2','i2','u4','i4','i8','f4','f8']:
            data[t+'scalar'] = 1 + numpy.arange(nrows, dtype=t)
            data[t+'vec'] = 1 + numpy.arange(nrows*nvec,dtype=t).reshape(nrows,nvec)
            arr = 1 + numpy.arange(nrows*ashape[0]*ashape[1],dtype=t)
            data[t+'arr'] = arr.reshape(nrows,ashape[0],ashape[1])

            for i in xrange(nrows):
                data[t+'obj'][i] = data[t+'vec'][i]


        # strings get padded when written to the fits file.  And the way I do
        # the read, I real all bytes (ala mrdfits) so the spaces are preserved.
        #
        # so for comparisons, we need to pad out the strings with blanks so we
        # can compare

        data['Sscalar'] = ['%-6s' % s for s in ['hello','world','good','bye']]
        data['Svec'][:,0] = '%-6s' % 'hello'
        data['Svec'][:,1] = '%-6s' % 'world'

        s = 1 + numpy.arange(nrows*ashape[0]*ashape[1])
        s = ['%-6s' % el for el in s]
        data['Sarr'] = numpy.array(s).reshape(nrows,ashape[0],ashape[1])

        if sys.version_info >= (3, 0, 0):
            data['Uscalar'] = ['%-6s' % s for s in ['hello','world','good','bye']]
            data['Uvec'][:,0] = '%-6s' % 'hello'
            data['Uvec'][:,1] = '%-6s' % 'world'

            s = 1 + numpy.arange(nrows*ashape[0]*ashape[1])
            s = ['%-6s' % el for el in s]
            data['Uarr'] = numpy.array(s).reshape(nrows,ashape[0],ashape[1])

        for i in xrange(nrows):
            data['Sobj'][i] = data['Sscalar'][i].rstrip()

        self.vardata = data

        #
        # for bitcol columns
        #
        nvec = 2
        ashape=(21,21)

        dtype=[('b1vec','?',nvec),

               ('b1arr','?',ashape)]

        nrows=4
        data=numpy.zeros(nrows, dtype=dtype)

        for t in ['b1']:
            data[t+'vec'] = (numpy.arange(nrows*nvec) % 2 == 0).astype('?').reshape(nrows,nvec)
            arr = (numpy.arange(nrows*ashape[0]*ashape[1]) % 2 == 0).astype('?')
            data[t+'arr'] = arr.reshape(nrows,ashape[0],ashape[1])

        self.bdata = data



    def testHeaderWriteRead(self):
        """
        Test a basic header write and read

        Note the other read/write tests also are checking header writing with
        a list of dicts
        """

        fname=tempfile.mktemp(prefix='fitsio-HeaderWrite-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                data=numpy.zeros(10)
                header={
                    'x':35,
                    'y':88.215,
                    'empty':'',
                    'funky':'35-8', # test old bug when strings look
                                    #like expressions
                    'name':'J. Smith',
                    'what': '89113e6', # test bug where converted to float
                    'und':None,
                    'binop':'25-3', # test string with binary operation in it
                    'unders':'1_000_000', # test string with underscore
                    'longs':lorem_ipsum,
                }
                fits.write_image(data, header=header)

                rh = fits[0].read_header()
                self.check_header(header, rh)

            with fitsio.FITS(fname) as fits:
                rh = fits[0].read_header()
                self.check_header(header, rh)

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testHeaderCommentPreserved(self):
        """
        Test that the comment is preserved after resetting the value
        """

        l1 = 'KEY1    =                   77 / My comment1'
        l2 = 'KEY2    =                   88 / My comment2'
        hdr=fitsio.FITSHDR()
        hdr.add_record(l1)
        hdr.add_record(l2)

        hdr['key1'] = 99
        self.assertEqual(hdr.get_comment('key1'), 'My comment1',
                         'comment not preserved')

    def testHeaderFromCards(self):
        """
        test generating a header from cards, writing it out and getting
        back what we put in
        """
        hdr_from_cards=fitsio.FITSHDR([
            "IVAL    =                   35 / integer value                                  ",
            "SHORTS  = 'hello world'                                                         ",
            "UND     =                                                                       ",
            "LONGS   = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiu&'",
            "CONTINUE  'smod tempor incididunt ut labore et dolore magna aliqua'             ",
            "DBL     =                 1.25                                                  ",
        ])
        header = [
            {'name':'ival','value':35,'comment':'integer value'},
            {'name':'shorts','value':'hello world'},
            {'name':'und','value':None},
            {'name':'longs','value':lorem_ipsum},
            {'name':'dbl','value':1.25},
        ]

        fname=tempfile.mktemp(prefix='fitsio-HeaderFromCars-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                data=numpy.zeros(10)
                fits.write_image(data, header=hdr_from_cards)

                rh = fits[0].read_header()
                self.compare_headerlist_header(header, rh)

            with fitsio.FITS(fname) as fits:
                rh = fits[0].read_header()
                self.compare_headerlist_header(header, rh)

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testCorruptContinue(self):
        """
        test with corrupt continue, just make sure it doesn't crash
        """
        with warnings.catch_warnings(record=True) as w:
            fname=tempfile.mktemp(prefix='fitsio-TestCorruptContinue-',suffix='.fits')

            hdr_from_cards=fitsio.FITSHDR([
                "IVAL    =                   35 / integer value                                  ",
                "SHORTS  = 'hello world'                                                         ",
                "CONTINUE= '        '           /   '&' / Current observing orogram              ",
                "UND     =                                                                       ",
                "DBL     =                 1.25                                                  ",
            ])

            try:
                with fitsio.FITS(fname,'rw',clobber=True) as fits:

                    fits.write(None, header=hdr_from_cards)

                rhdr = fitsio.read_header(fname)

            finally:
                if os.path.exists(fname):
                    os.remove(fname)

        with warnings.catch_warnings(record=True) as w:
            fname=tempfile.mktemp(prefix='fitsio-TestCorruptContinue-',suffix='.fits')

            hdr_from_cards=fitsio.FITSHDR([
                "IVAL    =                   35 / integer value                                  ",
                "SHORTS  = 'hello world'                                                         ",
                "PROGRAM = 'Setting the Scale: Determining the Absolute Mass Normalization and &'",
                "CONTINUE  'Scaling Relations for Clusters at z~0.1&'                            ",
                "CONTINUE  '&' / Current observing orogram                                       ",
                "UND     =                                                                       ",
                "DBL     =                 1.25                                                  ",
            ])

            try:
                with fitsio.FITS(fname,'rw',clobber=True) as fits:

                    fits.write(None, header=hdr_from_cards)

                rhdr = fitsio.read_header(fname)

            finally:
                if os.path.exists(fname):
                    os.remove(fname)


    def testImageWriteRead(self):
        """
        Test a basic image write, data and a header, then reading back in to
        check the values
        """

        fname=tempfile.mktemp(prefix='fitsio-ImageWrite-',suffix='.fits')
        dtypes=['u1','i1','u2','i2','<u4','i4','i8','>f4','f8']
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note mixing up byte orders a bit
                for dtype in dtypes:
                    data = numpy.arange(5*20,dtype=dtype).reshape(5,20)
                    header={'DTYPE':dtype,'NBYTES':data.dtype.itemsize}
                    fits.write_image(data, header=header)
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "images")

                    rh = fits[-1].read_header()
                    self.check_header(header, rh)

            with fitsio.FITS(fname) as fits:
                for i in xrange(len(dtypes)):
                    self.assertEqual(fits[i].is_compressed(), False, "not compressed")

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testImageWriteEmpty(self):
        """
        Test a basic image write, with no data and just a header, then reading
        back in to check the values
        """
        fname=tempfile.mktemp(prefix='fitsio-ImageWriteEmpty-',suffix='.fits')
        try:
            data=None
            header={'EXPTIME':120, 'OBSERVER':'Beatrice Tinsley','INSTRUME':'DECam','FILTER':'r'}
            with fitsio.FITS(fname,'rw',clobber=True, ignore_empty=True) as fits:
                for extname in ['CCD1','CCD2','CCD3','CCD4','CCD5','CCD6','CCD7','CCD8']:
                    fits.write_image(data, header=header)
                    rdata = fits[-1].read()
                    rh = fits[-1].read_header()
                    self.check_header(header, rh)
        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testImageWriteReadFromDims(self):
        """
        Test creating an image from dims and writing in place
        """

        fname=tempfile.mktemp(prefix='fitsio-ImageWriteFromDims-',suffix='.fits')
        dtypes=['u1','i1','u2','i2','<u4','i4','i8','>f4','f8']
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note mixing up byte orders a bit
                for dtype in dtypes:
                    data = numpy.arange(5*20,dtype=dtype).reshape(5,20)

                    fits.create_image_hdu(dims=data.shape,
                                          dtype=data.dtype)

                    fits[-1].write(data)
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "images")

            with fitsio.FITS(fname) as fits:
                for i in xrange(len(dtypes)):
                    self.assertEqual(fits[i].is_compressed(), False, "not compressed")

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testImageWriteReadFromDimsChunks(self):
        """
        Test creating an image and reading/writing chunks
        """

        fname=tempfile.mktemp(prefix='fitsio-ImageWriteFromDims-',suffix='.fits')
        dtypes=['u1','i1','u2','i2','<u4','i4','i8','>f4','f8']
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note mixing up byte orders a bit
                for dtype in dtypes:
                    data = numpy.arange(5*3,dtype=dtype).reshape(5,3)

                    fits.create_image_hdu(dims=data.shape,
                                          dtype=data.dtype)

                    chunk1 = data[0:2, :]
                    chunk2 = data[2: , :]

                    #
                    # first using scalar pixel offset
                    #

                    fits[-1].write(chunk1)

                    start=chunk1.size
                    fits[-1].write(chunk2, start=start)

                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "images")


                    #
                    # now using sequence, easier to calculate
                    #

                    fits.create_image_hdu(dims=data.shape,
                                          dtype=data.dtype)

                    # first using pixel offset
                    fits[-1].write(chunk1)

                    start=[2,0]
                    fits[-1].write(chunk2, start=start)

                    rdata2 = fits[-1].read()

                    self.compare_array(data, rdata2, "images")


            with fitsio.FITS(fname) as fits:
                for i in xrange(len(dtypes)):
                    self.assertEqual(fits[i].is_compressed(), False, "not compressed")

        finally:
            if os.path.exists(fname):
                os.remove(fname)


    def testImageSlice(self):
        """
        test reading an image slice
        """
        fname=tempfile.mktemp(prefix='fitsio-ImageSlice-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note mixing up byte orders a bit
                for dtype in ['u1','i1','u2','i2','<u4','i4','i8','>f4','f8']:
                    data = numpy.arange(16*20,dtype=dtype).reshape(16,20)
                    header={'DTYPE':dtype,'NBYTES':data.dtype.itemsize}
                    fits.write_image(data, header=header)
                    rdata = fits[-1][4:12, 9:17]

                    self.compare_array(data[4:12,9:17], rdata, "images")

                    rh = fits[-1].read_header()
                    self.check_header(header, rh)

        finally:
            if os.path.exists(fname):
                os.remove(fname)


    def testRiceTileCompressedWriteRead(self):
        """
        Test writing and reading a rice compressed image
        """
        nrows=30
        ncols=100
        tile_dims=[5,10]
        compress='rice'
        fname=tempfile.mktemp(prefix='fitsio-ImageWrite-',suffix='.fits.fz')
        dtypes = ['u1','i1','u2','i2','u4','i4','f4','f8']

        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note i8 not supported for compressed!

                for dtype in dtypes:
                    data = numpy.arange(nrows*ncols,dtype=dtype).reshape(nrows,ncols)
                    fits.write_image(data, compress=compress)
                    #fits.reopen()
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata,
                                       "%s compressed images ('%s')" % (compress,dtype))


                    fits.write_image(data, compress=compress, tile_dims=tile_dims)
                    #fits.reopen()
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata,
                                       ("%s tile dims compressed images "
                                        "('%s')" % (compress,dtype)))

            with fitsio.FITS(fname) as fits:
                for ii in xrange(len(dtypes)):
                    i=ii+1
                    self.assertEqual(fits[i].is_compressed(), True, "is compressed")

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testPLIOTileCompressedWriteRead(self):
        """
        test writing and readin PLIO compressed image
        """

        compress='plio'
        fname=tempfile.mktemp(prefix='fitsio-ImageWrite-',suffix='.fits.fz')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note i8 not supported for compressed!
                # also no writing unsigned, need to address
                dtypes = ['u1','i1','u2','i2','i4','f4','f8']

                for dtype in dtypes:
                    data = numpy.arange(5*20,dtype=dtype).reshape(5,20)
                    fits.write_image(data, compress=compress)
                    #fits.reopen()
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "%s compressed images ('%s')" % (compress,dtype))

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testGZIPTileCompressedWriteRead(self):
        """
        Test writing and reading gzip compressed image
        """

        compress='gzip'
        fname=tempfile.mktemp(prefix='fitsio-ImageWrite-',suffix='.fits.fz')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note i8 not supported for compressed!
                dtypes = ['u1','i1','u2','i2','u4','i4','f4','f8']

                for dtype in dtypes:
                    data = numpy.arange(5*20,dtype=dtype).reshape(5,20)
                    fits.write_image(data, compress=compress)
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "%s compressed images ('%s')" % (compress,dtype))

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testGZIP2TileCompressedWriteRead(self):
        """
        Test writing and reading gzip2 compressed image
        """

        compress='gzip_2'
        fname=tempfile.mktemp(prefix='fitsio-ImageWrite-',suffix='.fits.fz')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note i8 not supported for compressed!
                dtypes = ['u1','i1','u2','i2','u4','i4','f4','f8']

                for dtype in dtypes:
                    data = numpy.arange(5*20,dtype=dtype).reshape(5,20)
                    fits.write_image(data, compress=compress)
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "%s compressed images ('%s')" % (compress,dtype))

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testHCompressTileCompressedWriteRead(self):
        """
        Test writing and reading hcompress compressed image
        """

        compress='hcompress'
        fname=tempfile.mktemp(prefix='fitsio-ImageWrite-',suffix='.fits.fz')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                # note i8 not supported for compressed!
                dtypes = ['u1','i1','u2','i2','u4','i4','f4','f8']

                for dtype in dtypes:
                    if (dtype == 'u2') and ('SKIP_HCOMPRESS_U2_TEST' in os.environ):
                        continue
                    data = numpy.arange(5*20,dtype=dtype).reshape(5,20)
                    fits.write_image(data, compress=compress)
                    #fits.reopen()
                    rdata = fits[-1].read()

                    self.compare_array(data, rdata, "%s compressed images ('%s')" % (compress,dtype))

        finally:
            if os.path.exists(fname):
                os.remove(fname)



    def testWriteKeyDict(self):
        """
        test that write_key works using a standard key dict
        """

        fname=tempfile.mktemp(prefix='fitsio-WriteKeyDict-',suffix='.fits')
        nrows=3
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                im=numpy.zeros( (10,10), dtype='i2' )
                fits.write(im)

                keydict = {
                    'name':'test',
                    'value':35,
                    'comment':'keydict test',
                }
                fits[-1].write_key(**keydict)

                h = fits[-1].read_header()

                self.assertEqual(h['test'],keydict['value'])
                self.assertEqual(h.get_comment('test'),keydict['comment'])

        finally:
            if os.path.exists(fname):
                os.remove(fname)



    def testMoveByName(self):
        """
        test moving hdus by name
        """

        fname=tempfile.mktemp(prefix='fitsio-MoveByName-',suffix='.fits')
        nrows=3
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                data1=numpy.zeros(nrows,dtype=[('ra','f8'),('dec','f8')])
                data1['ra'] = numpy.random.random(nrows)
                data1['dec'] = numpy.random.random(nrows)
                fits.write_table(data1, extname='mytable')

                fits[-1].write_key("EXTVER", 1)

                data2=numpy.zeros(nrows,dtype=[('ra','f8'),('dec','f8')])
                data2['ra'] = numpy.random.random(nrows)
                data2['dec'] = numpy.random.random(nrows)

                fits.write_table(data2, extname='mytable')
                fits[-1].write_key("EXTVER", 2)

                hdunum1=fits.movnam_hdu('mytable',extver=1)
                self.assertEqual(hdunum1,2)
                hdunum2=fits.movnam_hdu('mytable',extver=2)
                self.assertEqual(hdunum2,3)

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testExtVer(self):
        """
        Test using extname and extver, all combinations I can think of
        """

        fname=tempfile.mktemp(prefix='fitsio-ExtVer-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                img1=numpy.arange(2*3,dtype='i4').reshape(2,3) + 5
                img2=numpy.arange(2*3,dtype='i4').reshape(2,3) + 6
                img3=numpy.arange(2*3,dtype='i4').reshape(2,3) + 7

                nrows=3
                data1=numpy.zeros(nrows,dtype=[('num','i4'),('ra','f8'),('dec','f8')])
                data1['num'] = 1
                data1['ra'] = numpy.random.random(nrows)
                data1['dec'] = numpy.random.random(nrows)

                data2=numpy.zeros(nrows,dtype=[('num','i4'),('ra','f8'),('dec','f8')])
                data2['num'] = 2
                data2['ra'] = numpy.random.random(nrows)
                data2['dec'] = numpy.random.random(nrows)

                data3=numpy.zeros(nrows,dtype=[('num','i4'),('ra','f8'),('dec','f8')])
                data3['num'] = 3
                data3['ra'] = numpy.random.random(nrows)
                data3['dec'] = numpy.random.random(nrows)


                fits.write_image(img1, extname='myimage', extver=1)
                fits.write_table(data1)
                fits.write_table(data2,extname='mytable', extver=1)
                fits.write_image(img2, extname='myimage', extver=2)
                fits.write_table(data3, extname='mytable',extver=2)
                fits.write_image(img3)

                d1  = fits[1].read()
                d2  = fits['mytable'].read()
                d2b = fits['mytable',1].read()
                d3  = fits['mytable',2].read()


                for f in data1.dtype.names:
                    self.compare_rec(data1, d1, "data1")
                    self.compare_rec(data2, d2, "data2")
                    self.compare_rec(data2, d2b, "data2b")
                    self.compare_rec(data3, d3, "data3")

                dimg1  = fits[0].read()
                dimg1b = fits['myimage',1].read()
                dimg2  = fits['myimage',2].read()
                dimg3  = fits[5].read()

                self.compare_array(img1, dimg1,"img1")
                self.compare_array(img1, dimg1b,"img1b")
                self.compare_array(img2, dimg2,"img2")
                self.compare_array(img3, dimg3,"img3")


        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testVariableLengthColumns(self):
        """
        Write and read variable length columns
        """

        for vstorage in ['fixed','object']:
            fname=tempfile.mktemp(prefix='fitsio-VarCol-',suffix='.fits')
            try:
                with fitsio.FITS(fname,'rw',clobber=True,vstorage=vstorage) as fits:
                    fits.write(self.vardata)


                    # reading multiple columns
                    d = fits[1].read()
                    self.compare_rec_with_var(self.vardata,d,"read all test '%s'" % vstorage)

                    cols=['u2scalar','Sobj']
                    d = fits[1].read(columns=cols)
                    self.compare_rec_with_var(self.vardata,d,"read all test subcols '%s'" % vstorage)

                    # one at a time
                    for f in self.vardata.dtype.names:
                        d = fits[1].read_column(f)
                        if fitsio.fitslib.is_object(self.vardata[f]):
                            self.compare_object_array(self.vardata[f], d,
                                                      "read all field '%s'" % f)

                    # same as above with slices
                    # reading multiple columns
                    d = fits[1][:]
                    self.compare_rec_with_var(self.vardata,d,"read all test '%s'" % vstorage)

                    d = fits[1][cols][:]
                    self.compare_rec_with_var(self.vardata,d,"read all test subcols '%s'" % vstorage)

                    # one at a time
                    for f in self.vardata.dtype.names:
                        d = fits[1][f][:]
                        if fitsio.fitslib.is_object(self.vardata[f]):
                            self.compare_object_array(self.vardata[f], d,
                                                      "read all field '%s'" % f)



                    #
                    # now same with sub rows
                    #

                    # reading multiple columns
                    rows = numpy.array([0,2])
                    d = fits[1].read(rows=rows)
                    self.compare_rec_with_var(self.vardata,d,"read subrows test '%s'" % vstorage,
                                              rows=rows)

                    d = fits[1].read(columns=cols, rows=rows)
                    self.compare_rec_with_var(self.vardata,d,"read subrows test subcols '%s'" % vstorage,
                                              rows=rows)

                    # one at a time
                    for f in self.vardata.dtype.names:
                        d = fits[1].read_column(f,rows=rows)
                        if fitsio.fitslib.is_object(self.vardata[f]):
                            self.compare_object_array(self.vardata[f], d,
                                                      "read subrows field '%s'" % f,
                                                      rows=rows)

                    # same as above with slices
                    # reading multiple columns
                    d = fits[1][rows]
                    self.compare_rec_with_var(self.vardata,d,"read subrows slice test '%s'" % vstorage,
                                              rows=rows)
                    d = fits[1][2:4]
                    self.compare_rec_with_var(self.vardata,d,"read slice test '%s'" % vstorage,
                                              rows=numpy.array([2,3]))

                    d = fits[1][cols][rows]
                    self.compare_rec_with_var(self.vardata,d,"read subcols subrows slice test '%s'" % vstorage,
                                              rows=rows)
                    d = fits[1][cols][2:4]
                    self.compare_rec_with_var(self.vardata,d,"read subcols slice test '%s'" % vstorage,
                                              rows=numpy.array([2,3]))

                    # one at a time
                    for f in self.vardata.dtype.names:
                        d = fits[1][f][rows]
                        if fitsio.fitslib.is_object(self.vardata[f]):
                            self.compare_object_array(self.vardata[f], d,
                                                      "read subrows field '%s'" % f,
                                                      rows=rows)
                        d = fits[1][f][2:4]
                        if fitsio.fitslib.is_object(self.vardata[f]):
                            self.compare_object_array(self.vardata[f], d,
                                                      "read slice field '%s'" % f,
                                                      rows=numpy.array([2,3]))




            finally:
                if os.path.exists(fname):
                    os.remove(fname)


    def testTableWriteRead(self):
        """
        Test a basic table write, data and a header, then reading back in to
        check the values
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWrite-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    fits.write_table(self.data, header=self.keys, extname='mytable')
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"testing write does not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

                d = fits[1].read()
                self.compare_rec(self.data, d, "table read/write")

                h = fits[1].read_header()
                self.compare_headerlist_header(self.keys, h)

            # see if our convenience functions are working
            fitsio.write(fname, self.data2,
                         extname="newext",
                         header={'ra':335.2,'dec':-25.2})
            d = fitsio.read(fname, ext='newext')
            self.compare_rec(self.data2, d, "table data2")
            # now test read_column
            with fitsio.FITS(fname) as fits:

                for f in self.data.dtype.names:
                    d = fits[1].read_column(f)
                    self.compare_array(self.data[f], d, "table 1 single field read '%s'" % f)

                for f in self.data2.dtype.names:
                    d = fits['newext'].read_column(f)
                    self.compare_array(self.data2[f], d, "table 2 single field read '%s'" % f)

                # now list of columns
                for cols in [['u2scalar','f4vec','Sarr'],
                             ['f8scalar','u2arr','Sscalar']]:
                    d = fits[1].read(columns=cols)
                    for f in d.dtype.names:
                        self.compare_array(self.data[f][:], d[f], "test column list %s" % f)


                    rows = [1,3]
                    d = fits[1].read(columns=cols, rows=rows)
                    for f in d.dtype.names:
                        self.compare_array(self.data[f][rows], d[f], "test column list %s row subset" % f)

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableColumnIndexScalar(self):
        """
        Test a basic table write, data and a header, then reading back in to
        check the values
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWrite-',suffix='.fits')

        with fitsio.FITS(fname,'rw',clobber=True) as fits:
            data = numpy.empty(1, dtype=[('Z', 'f8')])
            data['Z'][:] = 1.0
            fits.write_table(data)
            fits.write_table(data)
        try:
            with fitsio.FITS(fname,'r',clobber=True) as fits:
                # FIXME: change this to == 0 after
                # TableColumnSubset.__getitem__ handles this properly.
                assert fits[1]['Z'][0].ndim == 1
                pass
        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableFormatColumnSubset(self):
        """
        Test a basic table write, data and a header, then reading back in to
        check the values
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWrite-',suffix='.fits')

        with fitsio.FITS(fname,'rw',clobber=True) as fits:
            data = numpy.empty(1, dtype=[('Z', 'f8'), ('Z_PERSON', 'f8')])
            data['Z'][:] = 1.0
            data['Z_PERSON'][:] = 1.0
            fits.write_table(data)
            fits.write_table(data)
            fits.write_table(data)
        try:
            with fitsio.FITS(fname,'r',clobber=True) as fits:
                # assert we do not have an extra row of 'Z'
                sz = str(fits[2]['Z_PERSON']).split('\n')
                s  = str(fits[2][('Z_PERSON', 'Z')]).split('\n')
                assert len(sz) == len(s) - 1
        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableWriteDictOfArraysScratch(self):
        """
        This version creating the table from a dict of arrays, creating
        table first
        """

        fname=tempfile.mktemp(prefix='fitsio-TableDict-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    d={}
                    for n in self.data.dtype.names:
                        d[n] = self.data[n]

                    fits.write(d)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"write should not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            d = fitsio.read(fname)
            self.compare_rec(self.data, d, "list of dicts, scratch")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableWriteDictOfArrays(self):
        """
        This version creating the table from a dict of arrays
        """

        fname=tempfile.mktemp(prefix='fitsio-TableDict-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    fits.create_table_hdu(self.data, extname='mytable')

                    d={}
                    for n in self.data.dtype.names:
                        d[n] = self.data[n]

                    fits[-1].write(d)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"write should not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            d = fitsio.read(fname)
            self.compare_rec(self.data, d, "list of dicts")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)


    def testTableWriteDictOfArraysVar(self):
        """
        This version creating the table from a dict of arrays, variable
        lenght columns
        """

        fname=tempfile.mktemp(prefix='fitsio-TableDictVar-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    d={}
                    for n in self.vardata.dtype.names:
                        d[n] = self.vardata[n]

                    fits.write(d)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"write should not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            d = fitsio.read(fname)
            self.compare_rec_with_var(self.vardata,d,"dict of arrays, var")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)


    def testTableWriteListOfArraysScratch(self):
        """
        This version creating the table from the names and list, creating
        table first
        """

        fname=tempfile.mktemp(prefix='fitsio-TableListScratch-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    names = [n for n in self.data.dtype.names]
                    dlist = [self.data[n] for n in self.data.dtype.names]
                    fits.write(dlist, names=names)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"write should not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            d = fitsio.read(fname)
            self.compare_rec(self.data, d, "list of arrays, scratch")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)



    def testTableWriteListOfArrays(self):
        """
        Test a basic table write, data and a header, then reading back in to
        check the values
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWriteList-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    fits.create_table_hdu(self.data, extname='mytable')

                    columns = [n for n in self.data.dtype.names]
                    dlist = [self.data[n] for n in self.data.dtype.names]
                    fits[-1].write(dlist, columns=columns)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"write should not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            d = fitsio.read(fname, ext='mytable')
            self.compare_rec(self.data, d, "list of arrays")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableWriteListOfArraysVar(self):
        """
        This version creating the table from the names and list, variable
        lenght cols
        """

        fname=tempfile.mktemp(prefix='fitsio-TableListScratch-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    names = [n for n in self.vardata.dtype.names]
                    dlist = [self.vardata[n] for n in self.vardata.dtype.names]
                    fits.write(dlist, names=names)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"write should not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            d = fitsio.read(fname)
            self.compare_rec_with_var(self.vardata,d,"list of arrays, var")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableWriteBadString(self):
        """
        Test a basic table write, data and a header, then reading back in to
        check the values
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWriteBadString-',suffix='.fits')

        try:
            for d in ['S0','U0']:
                dt=[('s',d)]

                # old numpy didn't allow this dtype, so will throw
                # a TypeError for empty dtype
                try:
                    data = numpy.zeros(1, dtype=dt)
                    supported = True
                except TypeError:
                    supported = False

                if supported:
                    with fitsio.FITS(fname,'rw',clobber=True) as fits:

                        try:
                            fits.write(data)
                            got_error=False
                        except ValueError:
                            got_error=True

                        self.assertTrue(got_error == True,
                                        "expected an error for zero sized string")

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testTableIter(self):
        """
        Test iterating over rows of a table
        """

        fname=tempfile.mktemp(prefix='fitsio-TableIter-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                try:
                    fits.write_table(self.data, header=self.keys, extname='mytable')
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"testing write does not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

            # one row at a time
            with fitsio.FITS(fname) as fits:
                hdu = fits["mytable"]
                i=0
                for row_data in hdu:
                    self.compare_rec(self.data[i], row_data, "table data")
                    i+=1

        finally:
            if os.path.exists(fname):
                #pass
                os.remove(fname)

    def testAsciiTableWriteRead(self):
        """
        Test write and read for an ascii table
        """

        fname=tempfile.mktemp(prefix='fitsio-AsciiTableWrite-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                fits.write_table(self.ascii_data, table_type='ascii', header=self.keys, extname='mytable')

                # cfitsio always reports type as i4 and f8, period, even if if
                # written with higher precision.  Need to fix that somehow
                for f in self.ascii_data.dtype.names:
                    d = fits[1].read_column(f)
                    if d.dtype == numpy.float64:
                        # note we should be able to do 1.11e-16 in principle, but in practice
                        # we get more like 2.15e-16
                        self.compare_array_tol(self.ascii_data[f], d, 2.15e-16, "table field read '%s'" % f)
                    else:
                        self.compare_array(self.ascii_data[f], d, "table field read '%s'" % f)

                rows = [1,3]
                for f in self.ascii_data.dtype.names:
                    d = fits[1].read_column(f,rows=rows)
                    if d.dtype == numpy.float64:
                        self.compare_array_tol(self.ascii_data[f][rows], d, 2.15e-16,
                                               "table field read subrows '%s'" % f)
                    else:
                        self.compare_array(self.ascii_data[f][rows], d,
                                           "table field read subrows '%s'" % f)

                beg=1
                end=3
                for f in self.ascii_data.dtype.names:
                    d = fits[1][f][beg:end]
                    if d.dtype == numpy.float64:
                        self.compare_array_tol(self.ascii_data[f][beg:end], d, 2.15e-16,
                                               "table field read slice '%s'" % f)
                    else:
                        self.compare_array(self.ascii_data[f][beg:end], d,
                                           "table field read slice '%s'" % f)

                cols = ['i2scalar','f4scalar']
                for f in self.ascii_data.dtype.names:
                    data = fits[1].read(columns=cols)
                    for f in data.dtype.names:
                        d=data[f]
                        if d.dtype == numpy.float64:
                            self.compare_array_tol(self.ascii_data[f], d, 2.15e-16, "table subcol, '%s'" % f)
                        else:
                            self.compare_array(self.ascii_data[f], d, "table subcol, '%s'" % f)

                    data = fits[1][cols][:]
                    for f in data.dtype.names:
                        d=data[f]
                        if d.dtype == numpy.float64:
                            self.compare_array_tol(self.ascii_data[f], d, 2.15e-16, "table subcol, '%s'" % f)
                        else:
                            self.compare_array(self.ascii_data[f], d, "table subcol, '%s'" % f)

                rows=[1,3]
                for f in self.ascii_data.dtype.names:
                    data = fits[1].read(columns=cols,rows=rows)
                    for f in data.dtype.names:
                        d=data[f]
                        if d.dtype == numpy.float64:
                            self.compare_array_tol(self.ascii_data[f][rows], d, 2.15e-16,
                                                   "table subcol, '%s'" % f)
                        else:
                            self.compare_array(self.ascii_data[f][rows], d,
                                               "table subcol, '%s'" % f)

                    data = fits[1][cols][rows]
                    for f in data.dtype.names:
                        d=data[f]
                        if d.dtype == numpy.float64:
                            self.compare_array_tol(self.ascii_data[f][rows], d, 2.15e-16,
                                                   "table subcol/row, '%s'" % f)
                        else:
                            self.compare_array(self.ascii_data[f][rows], d,
                                               "table subcol/row, '%s'" % f)

                for f in self.ascii_data.dtype.names:

                    data = fits[1][cols][beg:end]
                    for f in data.dtype.names:
                        d=data[f]
                        if d.dtype == numpy.float64:
                            self.compare_array_tol(self.ascii_data[f][beg:end], d, 2.15e-16,
                                                   "table subcol/slice, '%s'" % f)
                        else:
                            self.compare_array(self.ascii_data[f][beg:end], d,
                                               "table subcol/slice, '%s'" % f)



        finally:
            if os.path.exists(fname):
                os.remove(fname)


    def testTableInsertColumn(self):
        """
        Insert a new column
        """

        fname=tempfile.mktemp(prefix='fitsio-TableInsertColumn-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                fits.write_table(self.data, header=self.keys, extname='mytable')

                d = fits[1].read()

                for n in d.dtype.names:
                    newname = n+'_insert'

                    fits[1].insert_column(newname, d[n])

                    newdata = fits[1][newname][:]

                    self.compare_array(d[n], newdata, "table single field insert and read '%s'" % n)

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testTableDeleteRowRange(self):
        """
        Test deleting a range of rows using the delete_rows method
        """

        fname=tempfile.mktemp(prefix='fitsio-TableDeleteRowRange-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write_table(self.data)

            rowslice = slice(1,3)
            with fitsio.FITS(fname,'rw') as fits:
                fits[1].delete_rows(rowslice)

            with fitsio.FITS(fname) as fits:
                d = fits[1].read()

            compare_data = self.data[ [0,3] ]
            self.compare_rec(compare_data, d, "delete row range")


        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testTableDeleteRows(self):
        """
        Test deleting specific set of rows using the delete_rows method
        """

        fname=tempfile.mktemp(prefix='fitsio-TableDeleteRows-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write_table(self.data)

            rows2delete = [1,3]
            with fitsio.FITS(fname,'rw') as fits:
                fits[1].delete_rows(rows2delete)

            with fitsio.FITS(fname) as fits:
                d = fits[1].read()

            compare_data = self.data[ [0,2] ]
            self.compare_rec(compare_data, d, "delete rows")


        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testTableResize(self):
        """
        Use the resize method to change the size of a table

        default values get filled in and these are tested
        """

        fname=tempfile.mktemp(prefix='fitsio-TableResize-',suffix='.fits')
        try:

            #
            # shrink from back
            #
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write_table(self.data)

            nrows = 2
            with fitsio.FITS(fname,'rw') as fits:
                fits[1].resize(nrows)

            with fitsio.FITS(fname) as fits:
                d = fits[1].read()

            compare_data = self.data[0:nrows]
            self.compare_rec(compare_data, d, "shrink from back")


            #
            # shrink from front
            #
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write_table(self.data)

            with fitsio.FITS(fname,'rw') as fits:
                fits[1].resize(nrows, front=True)

            with fitsio.FITS(fname) as fits:
                d = fits[1].read()

            compare_data = self.data[nrows-self.data.size:]
            self.compare_rec(compare_data, d, "shrink from front")


            # These don't get zerod

            nrows = 10
            add_data = numpy.zeros(nrows-self.data.size,dtype=self.data.dtype)
            add_data['i1scalar'] = -128
            add_data['i1vec'] = -128
            add_data['i1arr'] = -128
            add_data['u2scalar'] = 32768
            add_data['u2vec'] = 32768
            add_data['u2arr'] = 32768
            add_data['u4scalar'] = 2147483648
            add_data['u4vec'] = 2147483648
            add_data['u4arr'] = 2147483648


            #
            # expand at the back
            #
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write_table(self.data)
            with fitsio.FITS(fname,'rw') as fits:
                fits[1].resize(nrows)

            with fitsio.FITS(fname) as fits:
                d = fits[1].read()

            compare_data = numpy.hstack( (self.data, add_data) )
            self.compare_rec(compare_data, d, "expand at the back")

            #
            # expand at the front
            #
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write_table(self.data)
            with fitsio.FITS(fname,'rw') as fits:
                fits[1].resize(nrows, front=True)

            with fitsio.FITS(fname) as fits:
                d = fits[1].read()

            compare_data = numpy.hstack( (add_data, self.data) )
            # These don't get zerod
            self.compare_rec(compare_data, d, "expand at the front")


        finally:
            if os.path.exists(fname):
                os.remove(fname)



    def testSlice(self):
        """
        Test reading by slice
        """

        fname=tempfile.mktemp(prefix='fitsio-TableAppend-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                # initial write
                fits.write_table(self.data)

                # test reading single columns
                for f in self.data.dtype.names:
                    d = fits[1][f][:]
                    self.compare_array(self.data[f], d, "test read all rows %s column subset" % f)

                # test reading row subsets
                rows = [1,3]
                for f in self.data.dtype.names:
                    d = fits[1][f][rows]
                    self.compare_array(self.data[f][rows], d, "test %s row subset" % f)
                for f in self.data.dtype.names:
                    d = fits[1][f][1:3]
                    self.compare_array(self.data[f][1:3], d, "test %s row slice" % f)

                # now list of columns
                cols=['u2scalar','f4vec','Sarr']
                d = fits[1][cols][:]
                for f in d.dtype.names:
                    self.compare_array(self.data[f][:], d[f], "test column list %s" % f)


                cols=['u2scalar','f4vec','Sarr']
                d = fits[1][cols][rows]
                for f in d.dtype.names:
                    self.compare_array(self.data[f][rows], d[f], "test column list %s row subset" % f)

                cols=['u2scalar','f4vec','Sarr']
                d = fits[1][cols][1:3]
                for f in d.dtype.names:
                    self.compare_array(self.data[f][1:3], d[f], "test column list %s row slice" % f)



        finally:
            if os.path.exists(fname):
                os.remove(fname)




    def testTableAppend(self):
        """
        Test creating a table and appending new rows.
        """

        fname=tempfile.mktemp(prefix='fitsio-TableAppend-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                # initial write
                fits.write_table(self.data, header=self.keys, extname='mytable')
                # now append
                data2 = self.data.copy()
                data2['f4scalar'] = 3
                fits[1].append(data2)

                d = fits[1].read()
                self.assertEqual(d.size, self.data.size*2)

                self.compare_rec(self.data, d[0:self.data.size], "Comparing initial write")
                self.compare_rec(data2, d[self.data.size:], "Comparing appended data")

                h = fits[1].read_header()
                self.compare_headerlist_header(self.keys, h)

        finally:
            if os.path.exists(fname):
                os.remove(fname)



    def testTableSubsets(self):
        """
        testing reading subsets
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWrite-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                fits.write_table(self.data, header=self.keys, extname='mytable')


                rows = [1,3]
                d = fits[1].read(rows=rows)
                self.compare_rec_subrows(self.data, d, rows, "table subset")
                columns = ['i1scalar','f4arr']
                d = fits[1].read(columns=columns, rows=rows)

                for f in columns:
                    d = fits[1].read_column(f,rows=rows)
                    self.compare_array(self.data[f][rows], d, "row subset, multi-column '%s'" % f)
                for f in self.data.dtype.names:
                    d = fits[1].read_column(f,rows=rows)
                    self.compare_array(self.data[f][rows], d, "row subset, column '%s'" % f)

        finally:
            if os.path.exists(fname):
                os.remove(fname)



    def testGZWriteRead(self):
        """
        Test a basic table write, data and a header, then reading back in to
        check the values

        this code all works, but the file is zere size when done!
        """

        fname=tempfile.mktemp(prefix='fitsio-GZTableWrite-',suffix='.fits.gz')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                fits.write_table(self.data, header=self.keys, extname='mytable')

                d = fits[1].read()
                self.compare_rec(self.data, d, "gzip write/read")

                h = fits[1].read_header()
                for entry in self.keys:
                    name=entry['name'].upper()
                    value=entry['value']
                    hvalue = h[name]
                    if isinstance(hvalue,str):
                        hvalue = hvalue.strip()
                    self.assertEqual(value,hvalue,"testing header key '%s'" % name)

                    if 'comment' in entry:
                        self.assertEqual(entry['comment'].strip(),
                                         h.get_comment(name).strip(),
                                         "testing comment for header key '%s'" % name)
            stat=os.stat(fname)
            self.assertNotEqual(stat.st_size, 0, "Making sure the data was flushed to disk")
        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testBz2Read(self):
        '''
        Write a normal .fits file, run bzip2 on it, then read the bz2
        file and verify that it's the same as what we put in; we don't
        [currently support or] test *writing* bzip2.
        '''

        if 'SKIP_BZIP_TEST' in os.environ:
            if sys.version_info >= (2,7,0):
                self.skipTest("skipping bzip tests")
            else:
                # skipTest only works for python 2.7+
                # just return
                return

        fname=tempfile.mktemp(prefix='fitsio-BZ2TableWrite-',suffix='.fits')
        bzfname = fname + '.bz2'

        try:
            fits = fitsio.FITS(fname,'rw',clobber=True)
            fits.write_table(self.data, header=self.keys, extname='mytable')
            fits.close()

            os.system('bzip2 %s' % fname)
            f2 = fitsio.FITS(bzfname)
            d = f2[1].read()
            self.compare_rec(self.data, d, "bzip2 read")

            h = f2[1].read_header()
            for entry in self.keys:
                name=entry['name'].upper()
                value=entry['value']
                hvalue = h[name]
                if isinstance(hvalue,str):
                    hvalue = hvalue.strip()
                self.assertEqual(value,hvalue,"testing header key '%s'" % name)
                if 'comment' in entry:
                    self.assertEqual(entry['comment'].strip(),
                                     h.get_comment(name).strip(),
                                     "testing comment for header key '%s'" % name)
        except:
            import traceback
            traceback.print_exc()
            self.assertTrue(False, 'Exception in testing bzip2 reading')
        finally:
            if os.path.exists(fname):
                os.remove(fname)
            if os.path.exists(bzfname):
                os.remove(bzfname)
            pass

    def testChecksum(self):
        """
        test that checksumming works
        """

        fname=tempfile.mktemp(prefix='fitsio-Checksum-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                fits.write_table(self.data, header=self.keys, extname='mytable')
                fits[1].write_checksum()
                fits[1].verify_checksum()
        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testTrimStrings(self):
        """
        test mode where we strim strings on read
        """
        fname=tempfile.mktemp(prefix='fitsio-Trim-',suffix='.fits')
        dt=[('fval','f8'),('name','S15'),('vec','f4',2)]
        n=3
        data=numpy.zeros(n, dtype=dt)
        data['fval'] = numpy.random.random(n)
        data['vec'] = numpy.random.random(n*2).reshape(n,2)

        data['name'] = ['mike','really_long_name_to_fill','jan']

        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write(data)

            for onconstruct in [True,False]:
                if onconstruct:
                    ctrim=True
                    otrim=False
                else:
                    ctrim=False
                    otrim=True

                with fitsio.FITS(fname,'rw', trim_strings=ctrim) as fits:

                    if ctrim:
                        dread=fits[1][:]
                        self.compare_rec(
                            data,
                            dread,
                            "trimmed strings constructor",
                        )

                        dname=fits[1]['name'][:]
                        self.compare_array(
                            data['name'],
                            dname,
                            "trimmed strings col read, constructor",
                        )
                        dread=fits[1][ ['name'] ][:]
                        self.compare_array(
                            data['name'],
                            dread['name'],
                            "trimmed strings col read, constructor",
                        )



                    dread=fits[1].read(trim_strings=otrim)
                    self.compare_rec(
                        data,
                        dread,
                        "trimmed strings keyword",
                    )
                    dname=fits[1].read(columns='name', trim_strings=otrim)
                    self.compare_array(
                        data['name'],
                        dname,
                        "trimmed strings col keyword",
                    )
                    dread=fits[1].read(columns=['name'], trim_strings=otrim)
                    self.compare_array(
                        data['name'],
                        dread['name'],
                        "trimmed strings col keyword",
                    )



            # convenience function
            dread=fitsio.read(fname, trim_strings=True)
            self.compare_rec(
                data,
                dread,
                "trimmed strings convenience function",
            )
            dname=fitsio.read(fname, columns='name', trim_strings=True)
            self.compare_array(
                data['name'],
                dname,
                "trimmed strings col convenience function",
            )
            dread=fitsio.read(fname, columns=['name'], trim_strings=True)
            self.compare_array(
                data['name'],
                dread['name'],
                "trimmed strings col convenience function",
            )



        finally:
            if os.path.exists(fname):
                os.remove(fname)


    def testLowerUpper(self):
        """
        test forcing names to upper and lower
        """
        fname=tempfile.mktemp(prefix='fitsio-LowerUpper-',suffix='.fits')
        dt=[('MyName','f8'),('StuffThings','i4'),('Blah','f4')]
        data=numpy.zeros(3, dtype=dt)
        data['MyName'] = numpy.random.random(data.size)
        data['StuffThings'] = numpy.random.random(data.size)
        data['Blah'] = numpy.random.random(data.size)

        lnames = [n.lower() for n in data.dtype.names]
        unames = [n.upper() for n in data.dtype.names]

        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write(data)

            for i in [1,2]:
                if i == 1:
                    lower=True
                    upper=False
                else:
                    lower=False
                    upper=True

                with fitsio.FITS(fname,'rw', lower=lower, upper=upper) as fits:
                    for rows in [None, [1,2]]:

                        d=fits[1].read(rows=rows)
                        self.compare_names(d.dtype.names,data.dtype.names,
                                           lower=lower,upper=upper)


                        d=fits[1].read(rows=rows, columns=['MyName','stuffthings'])
                        self.compare_names(d.dtype.names,data.dtype.names[0:2],
                                           lower=lower,upper=upper)

                        d = fits[1][1:2]
                        self.compare_names(d.dtype.names,data.dtype.names,
                                           lower=lower,upper=upper)

                        if rows is not None:
                            d = fits[1][rows]
                        else:
                            d = fits[1][:]
                        self.compare_names(d.dtype.names,data.dtype.names,
                                           lower=lower,upper=upper)

                        if rows is not None:
                            d = fits[1][['myname','stuffthings']][rows]
                        else:
                            d = fits[1][['myname','stuffthings']][:]
                        self.compare_names(d.dtype.names,data.dtype.names[0:2],
                                           lower=lower,upper=upper)

                # using overrides
                with fitsio.FITS(fname,'rw') as fits:
                    for rows in [None, [1,2]]:

                        d=fits[1].read(rows=rows, lower=lower, upper=upper)
                        self.compare_names(d.dtype.names,data.dtype.names,
                                           lower=lower,upper=upper)


                        d=fits[1].read(rows=rows, columns=['MyName','stuffthings'],
                                       lower=lower,upper=upper)
                        self.compare_names(d.dtype.names,data.dtype.names[0:2],
                                           lower=lower,upper=upper)



                for rows in [None, [1,2]]:
                    d=fitsio.read(fname, rows=rows, lower=lower, upper=upper)
                    self.compare_names(d.dtype.names,data.dtype.names,
                                       lower=lower,upper=upper)

                    d=fitsio.read(fname, rows=rows, columns=['MyName','stuffthings'],
                                  lower=lower, upper=upper)
                    self.compare_names(d.dtype.names,data.dtype.names[0:2],
                                       lower=lower,upper=upper)


        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testReadRaw(self):
        """
        testing reading the file as raw bytes
        """
        fname=tempfile.mktemp(prefix='fitsio-readraw-',suffix='.fits')

        dt=[('MyName','f8'),('StuffThings','i4'),('Blah','f4')]
        data=numpy.zeros(3, dtype=dt)
        data['MyName'] = numpy.random.random(data.size)
        data['StuffThings'] = numpy.random.random(data.size)
        data['Blah'] = numpy.random.random(data.size)

        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                fits.write(data)
                raw1 = fits.read_raw()

            with fitsio.FITS('mem://', 'rw') as fits:
                fits.write(data)
                raw2 = fits.read_raw()

            f = open(fname, 'rb')
            raw3 = f.read()
            f.close()

            self.assertEqual(raw1, raw2)
            self.assertEqual(raw1, raw3)
        except:
            import traceback
            traceback.print_exc()
            self.assertTrue(False, 'Exception in testing read_raw')

    def testTableBitcolReadWrite(self):
        """
        Test basic write/read with bitcols
        """

        fname=tempfile.mktemp(prefix='fitsio-TableWriteBitcol-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:
                try:
                    fits.write_table(self.bdata, extname='mytable', write_bitcols=True)
                    write_success=True
                except:
                    write_success=False

                self.assertTrue(write_success,"testing write does not raise an error")
                if not write_success:
                    self.skipTest("cannot test result if write failed")

                d=fits[1].read()
                self.compare_rec(self.bdata, d, "table read/write")

            # now test read_column
            with fitsio.FITS(fname) as fits:

                for f in self.bdata.dtype.names:
                    d = fits[1].read_column(f)
                    self.compare_array(self.bdata[f], d, "table 1 single field read '%s'" % f)

                # now list of columns
                for cols in [['b1vec','b1arr']]:
                    d = fits[1].read(columns=cols)
                    for f in d.dtype.names:
                        self.compare_array(self.bdata[f][:], d[f], "test column list %s" % f)

                    rows = [1,3]
                    d = fits[1].read(columns=cols, rows=rows)
                    for f in d.dtype.names:
                        self.compare_array(self.bdata[f][rows], d[f], "test column list %s row subset" % f)

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def testTableBitcolAppend(self):
        """
        Test creating a table with bitcol support and appending new rows.
        """

        fname=tempfile.mktemp(prefix='fitsio-TableAppendBitcol-',suffix='.fits')
        try:
            with fitsio.FITS(fname,'rw',clobber=True) as fits:

                # initial write
                fits.write_table(self.bdata, extname='mytable', write_bitcols=True)
                # now append
                bdata2 = self.bdata.copy()
                fits[1].append(bdata2)

                d = fits[1].read()
                self.assertEqual(d.size, self.bdata.size*2)

                self.compare_rec(self.bdata, d[0:self.data.size], "Comparing initial write")
                self.compare_rec(bdata2, d[self.data.size:], "Comparing appended data")

        finally:
            if os.path.exists(fname):
                os.remove(fname)

    def compare_names(self, read_names, true_names, lower=False, upper=False):
        for nread,ntrue in zip(read_names,true_names):
            if lower:
                tname = ntrue.lower()
                mess="lower: '%s' vs '%s'" % (nread,tname)
            else:
                tname = ntrue.upper()
                mess="upper: '%s' vs '%s'" % (nread,tname)
            self.assertEqual(nread, tname, mess)

    def check_header(self, header, rh):
        for k in header:
            v = header[k]
            rv = rh[k]
            if isinstance(rv,str):
                v = v.strip()
                rv = rv.strip()
            self.assertEqual(v,rv,"testing equal key '%s'" % k)


    def compare_headerlist_header(self, header_list, header):
        """
        The first is a list of dicts, second a FITSHDR
        """
        for entry in header_list:
            name=entry['name'].upper()
            value=entry['value']
            hvalue = header[name]
            if isinstance(hvalue,str):
                hvalue = hvalue.strip()
            self.assertEqual(value,hvalue,"testing header key '%s'" % name)

            if 'comment' in entry:
                self.assertEqual(entry['comment'].strip(),
                                 header.get_comment(name).strip(),
                                 "testing comment for header key '%s'" % name)

    def _cast_shape(self, shape):
        if len(shape) == 2 and shape[1] == 1:
            return (shape[0],)
        elif shape == (1,):
            return tuple()
        else:
            return shape

    def compare_array_tol(self, arr1, arr2, tol, name):
        self.assertEqual(arr1.shape, arr2.shape,
                         "testing arrays '%s' shapes are equal: "
                         "input %s, read: %s" % (name, arr1.shape, arr2.shape))

        adiff = numpy.abs( (arr1-arr2)/arr1 )
        maxdiff = adiff.max()
        res=numpy.where(adiff  > tol)
        for i,w in enumerate(res):
            self.assertEqual(w.size,0,
                             "testing array '%s' dim %d are "
                             "equal within tolerance %e, found "
                             "max diff %e" % (name,i,tol,maxdiff))


    def compare_array(self, arr1, arr2, name):
        arr1_shape = self._cast_shape(arr1.shape)
        arr2_shape = self._cast_shape(arr2.shape)

        self.assertEqual(arr1_shape, arr2_shape,
                         "testing arrays '%s' shapes are equal: "
                         "input %s, read: %s" % (name, arr1_shape, arr2_shape))

        if sys.version_info >= (3, 0, 0) and arr1.dtype.char == 'S':
            _arr1 = arr1.astype('U')
        else:
            _arr1 = arr1
        res=numpy.where(_arr1 != arr2)
        for i,w in enumerate(res):
            self.assertEqual(w.size,0,"testing array '%s' dim %d are equal" % (name,i))

    def compare_rec(self, rec1, rec2, name):
        for f in rec1.dtype.names:
            rec1_shape = self._cast_shape(rec1[f].shape)
            rec2_shape = self._cast_shape(rec2[f].shape)
            self.assertEqual(rec1_shape, rec2_shape,
                             "testing '%s' field '%s' shapes are equal: "
                             "input %s, read: %s" % (
                                name, f, rec1_shape, rec2_shape))

            if sys.version_info >= (3, 0, 0) and rec1[f].dtype.char == 'S':
                # for python 3, we get back unicode always
                _rec1f = rec1[f].astype('U')
            else:
                _rec1f = rec1[f]

            res=numpy.where(_rec1f != rec2[f])
            for w in res:
                self.assertEqual(w.size,0,"testing column %s" % f)

    def compare_rec_subrows(self, rec1, rec2, rows, name):
        for f in rec1.dtype.names:
            rec1_shape = self._cast_shape(rec1[f][rows].shape)
            rec2_shape = self._cast_shape(rec2[f].shape)

            self.assertEqual(rec1_shape, rec2_shape,
                             "testing '%s' field '%s' shapes are equal: "
                             "input %s, read: %s" % (
                                name, f, rec1_shape, rec2_shape))

            if sys.version_info >= (3, 0, 0) and rec1[f].dtype.char == 'S':
                # for python 3, we get back unicode always
                _rec1frows = rec1[f][rows].astype('U')
            else:
                _rec1frows = rec1[f][rows]

            res=numpy.where(_rec1frows != rec2[f])
            for w in res:
                self.assertEqual(w.size,0,"testing column %s" % f)

            #self.assertEqual(2,3,"on purpose error")

    def compare_rec_with_var(self, rec1, rec2, name, rows=None):
        """

        First one *must* be the one with object arrays

        Second can have fixed length

        both should be same number of rows

        """

        if rows is None:
            rows = arange(rec2.size)
            self.assertEqual(rec1.size,rec2.size,
                             "testing '%s' same number of rows" % name)

        # rec2 may have fewer fields
        for f in rec2.dtype.names:

            # f1 will have the objects
            if fitsio.fitslib.is_object(rec1[f]):
                self.compare_object_array(rec1[f], rec2[f],
                                          "testing '%s' field '%s'" % (name,f),
                                          rows=rows)
            else:
                self.compare_array(rec1[f][rows], rec2[f],
                                   "testing '%s' num field '%s' equal" % (name,f))

    def compare_object_array(self, arr1, arr2, name, rows=None):
        """
        The first must be object
        """
        if rows is None:
            rows = arange(arr1.size)

        for i,row in enumerate(rows):
            if (sys.version_info >= (3, 0, 0) and isinstance(arr2[i], bytes)) or isinstance(arr2[i], str):
                if sys.version_info >= (3, 0, 0) and isinstance(arr1[row], bytes):
                    _arr1row = arr1[row].decode('ascii')
                else:
                    _arr1row = arr1[row]
                self.assertEqual(_arr1row,arr2[i],
                                "%s str el %d equal" % (name,i))
            else:
                delement = arr2[i]
                orig = arr1[row]
                s=len(orig)
                self.compare_array(orig, delement[0:s],
                                   "%s num el %d equal" % (name,i))

    def compare_rec_with_var_subrows(self, rec1, rec2, name, rows):
        """

        Second one must be the one with object arrays

        """
        for f in rec1.dtype.names:
            if fitsio.fitslib.is_object(rec2[f]):

                for i in xrange(rec2.size):
                    if isinstance(rec2[f][i],str):
                        self.assertEqual(rec1[f][i],rec2[f][i],
                                        "testing '%s' str field '%s' el %d equal" % (name,f,i))
                    else:
                        delement = rec1[f][i]
                        orig = rec2[f][i]
                        s=orig.size
                        self.compare_array(orig, delement[0:s],
                                           "testing '%s' num field '%s' el %d equal" % (name,f,i))
            else:
                self.compare_array(rec1[f], rec2[f],
                                   "testing '%s' num field '%s' equal" % (name,f))





if __name__ == '__main__':
    test()
