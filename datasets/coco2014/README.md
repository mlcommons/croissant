WARNING: `metadata.json` is  incomplete and does not fully defines the COCO2014 dataset. It lacks the `recordSet` definitions that would enable automatic loading of the data.

`metadata.json` provides an example on how splits can be defined at the `FileSet` level:

 - either by specifying the split name directly (on `imageinfo` `FileSet` in this example); 
 - or by extracting the name of the split from the file path (in the other `FileSet`s in this example).
