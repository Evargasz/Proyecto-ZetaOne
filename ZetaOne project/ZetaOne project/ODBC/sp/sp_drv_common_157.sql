use sybsystemprocs
go

if exists (SELECT * FROM sysobjects WHERE name = 'sp_drv_column_default')
begin
        drop procedure sp_drv_column_default
end
go

create procedure sp_drv_column_default(@obj_id int, @default_value varchar (1024) output)
as
    declare @text_count              int
    declare @default_holder          varchar (255)
    declare @rownum                  int
    declare @create_default_starts   int
    declare @default_starts          int
    declare @actual_default_starts   int
    declare @as_starts               int
    declare @length                  int
    declare @check_case_one          int
    declare @check_last_char         int
    declare @linefeed_char           char (2)
    declare @last_char               char (2)

    /* make sure @default_value starts out as empty */
    SELECT @default_value = null

    /* initialize @check_case_one to false (0) */
    SELECT @check_case_one = 0

    /* initialize @check_last_char to false (0) */
    SELECT @check_last_char = 0

    /* initialize the @linefeed_char variable to linefeed */
    SELECT @linefeed_char = char (10)

    /* Find out how many rows there are in syscomments defining the 
       default. If there are none, then we return a null */
    SELECT @text_count = count (*) FROM syscomments
        WHERE id = @obj_id

    if @text_count = 0
    begin
        return 0
    end

    /* See if the object is hidden (SYSCOM_TEXT_HIDDEN will be set).
       If it is, best we can do is return null */
    if exists (SELECT 1 FROM syscomments WHERE (status & 1 = 1)
        AND id = @obj_id)
    begin
        return 0
    end

    SELECT @rownum = 1
    declare default_value_cursor cursor for
        SELECT text FROM syscomments WHERE id = @obj_id
        order by number, colid2, colid

    open default_value_cursor

    fetch default_value_cursor into @default_holder
 
    while (@@sqlstatus = 0)
    begin

        if @rownum = 1
        begin
            /* find the default value                                       
            **  Note that ASE stores default values in more than one way:    
            **    1. If a client declares the column default value in the     
            **       table definition, ASE will store the word DEFAULT (in    
            **       all caps) followed by the default value, exactly as the  
            **       user entered it (meaning it will include quotes, if the
            **       value was a string constant). This DEFAULT word will
            **       be in all caps even if the user did something like this:
            **           create table foo (col1 varchar (10) DeFaULT 'bar')
            **    2. If a client does sp_bindefault to bind a default to 
            **       a column, ASE will include the text of the create default
            **       command, as entered. So, if the client did the following:
            **           create DeFAULt foo aS 'bar'
            **       that is exactly what ASE will place in the text column
            **       of syscomments.
            **       In this case, too, we have to be careful because ASE
            **       will sometimes include a newline character 
            **       at the end of the create default statement. This
            **       can happen if a client uses C isql to type in the
            **       create default command (if it comes in through java, then
            **       the newline AND null are not present).
            **  Because of this, we have to be careful when trying to parse out
            **  the default value. 
            */

            SELECT @length = char_length (@default_holder)
            SELECT @create_default_starts =
                charindex ('create default', lower(@default_holder))
            SELECT @as_starts = charindex(' as ', lower(@default_holder))
            SELECT @default_starts = charindex ('DEFAULT', @default_holder)

            if (@create_default_starts != 0 AND @as_starts != 0) 
            begin

                /* If we get here, then we likely have case (2) above.
                ** However, it's still possible that the client did something
                ** like this:
                **     create table foo (col1 varchar (20) default 
                **         'create default foo as bar')            
                ** The following if block accounts for that possibility  
                */

                if (@default_starts != 0 and
                  @default_starts < @create_default_starts)
                begin
                    SELECT @check_case_one = 1
                end
                else
                begin
                    SELECT @actual_default_starts = @as_starts + 4
                    SELECT @check_last_char = 1

                    /* set @default_starts to 0 so we don't fall into the
                    ** next if block. This is important because we would
                    ** fall into the next if block if a client had used the
                    ** following sql:
                    **     CREATE DEFAULT foo as 'bar'               
                    */
                    SELECT @default_starts = 0
                end
            end

            if (@default_starts != 0 OR @check_case_one != 0)
                /* If we get here, then we have case (1) above */
 
                SELECT @actual_default_starts = @default_starts + 7
           
            /* The ltrim removes any left-side blanks, because ASE appears
            ** to insert several blanks between the word DEFAULT AND the
            ** start of the default vale */
 
            SELECT @default_holder = 
                ltrim(substring
                    (@default_holder, @actual_default_starts, @length))

        end

        SELECT @default_value = @default_value + @default_holder
        SELECT @rownum = @rownum + 1

        fetch default_value_cursor into @default_holder

    end /* while loop */

    close default_value_cursor

    /* trim off any right-side blanks */
    SELECT @default_value = rtrim (@default_value)
 
    /* trim off the newline AND null characters, if they're the last 
    ** two characters in what remains 
    */
    if (@check_last_char = 1)
    begin

        SELECT @length = char_length (@default_value)
        SELECT @last_char = substring (@default_value, @length, 1)
        if (@last_char = @linefeed_char)
            SELECT @default_value = substring (@default_value, 1, (@length - 1))
    end
   
    return 0


go
exec sp_procxmode 'sp_drv_column_default', 'anymode'
go
grant execute on sp_drv_column_default to public
go

dump transaction sybsystemprocs with truncate_only
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_typeinfo')
begin
      drop procedure sp_drv_typeinfo
end
go


create procedure sp_drv_typeinfo(@sstype int=0)
as
        declare @curiso int
        SELECT @curiso=@@isolation
        if @@isolation = 0
        begin
               
                set transaction isolation level 1
        end

            if @sstype = 0
              SELECT literal_prefix, literal_suffix, case_sensitive, searchable, unsigned_attribute, num_prec_radix, ss_dtype FROM sybsystemprocs.dbo.spt_datatype_info
        else
              SELECT literal_prefix, literal_suffix, case_sensitive, searchable, unsigned_attribute, num_prec_radix FROM sybsystemprocs.dbo.spt_datatype_info WHERE ss_dtype = @sstype
        /*Not necessary, just for more clear logic */
        if @curiso = 0
        begin
                set transaction isolation level 0
        end


        return(0)
go

exec sp_procxmode 'sp_drv_typeinfo', 'anymode'
go
grant execute on sp_drv_typeinfo to public
go
dump tran master with truncate_only
go

dump transaction sybsystemprocs with truncate_only
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_localtypename')
begin
      drop procedure sp_localtypename
end
go

create procedure sp_localtypename(@sstype int)
as

      declare @curiso int
      SELECT @curiso=@@isolation
      if @@isolation = 0
      begin
            
            set transaction isolation level 1
      end

      SELECT local_type_name FROM sybsystemprocs.dbo.spt_datatype_info WHERE ss_dtype = @sstype      

      if @curiso = 0
      begin
            set transaction isolation level 0
      end
      return(0)
go

exec sp_procxmode 'sp_localtypename', 'anymode'
go
grant execute on sp_localtypename to public
go
dump tran master with truncate_only
go

dump transaction sybsystemprocs with truncate_only
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_getsortorder')
begin
      drop procedure sp_drv_getsortorder
end
go

create procedure sp_drv_getsortorder
as
declare @id int
SELECT @id=id FROM master.dbo.syscharsets 
      where id=(SELECT value FROM master.dbo.sysconfigures WHERE name like '%default sortorder id%') 
      and description like '%insensitive%'
if isnull(@id,0)=0
begin
 SELECT @id=0
end
SELECT @id
go

exec sp_procxmode 'sp_drv_getsortorder', 'anymode'
go
grant execute on sp_drv_getsortorder to public
go

dump transaction sybsystemprocs with truncate_only
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_gettypes')
begin
      drop procedure sp_drv_gettypes
end
go

create procedure sp_drv_gettypes(@sstype int=0,@usertype int=0)
as
declare @cmd varchar(500)

SELECT @cmd=" SELECT name=case 
      when b.usertype=18 then 'sysname' 
      when b.usertype=25 then 'nvarchar' 
      when b.usertype=42 then 'longsysname' 
      when b.usertype=80 then 'timestamp' 
      when b.usertype=24 then 'nchar' 
      when a.ss_dtype=111 then 'datetimn' 
      when a.ss_dtype=109 then 'floatn' 
      else local_type_name end,
      a.ss_dtype,
      b.usertype 
      from sybsystemprocs.dbo.spt_datatype_info a,
      systypes b 
      where a.ss_dtype=b.type  "

if @sstype>0 AND @usertype>0
begin
      SELECT @cmd = @cmd + " AND a.ss_dtype="+convert(varchar(10),@sstype)+"  AND b.usertype="+convert(varchar(10),@usertype)

end
else if @sstype=0 AND @usertype=0
begin
      SELECT @cmd=@cmd
end
else if @sstype=0
begin
      SELECT @cmd = @cmd + "  AND b.usertype="+convert(varchar(10),@usertype)

end
else if @usertype=0
begin
      SELECT @cmd = @cmd + " AND a.ss_dtype="+convert(varchar(10),@sstype)
end

execute(@cmd)

go

dump transaction master with truncate_only
go

dump transaction sybsystemprocs with truncate_only
go
use sybsystemprocs
go

if exists (SELECT * FROM sysobjects WHERE name = 'sp_drv_bcpmetadata')
    begin
    drop procedure sp_drv_bcpmetadata
    end
go


CREATE PROCEDURE sp_drv_bcpmetadata (
@table_name  varchar(771),
@table_owner        varchar(32 ) = null,
@table_qualifier    varchar(32 ) = null
)
AS


    declare @msg               varchar(250)
    declare @full_table_name   varchar(1542)
    declare @table_id          int
    declare @sysstat2          int
    declare @table_lock_scheme bit
    declare @allow_wide_dol    bit
    declare @checktemptable    int
    declare @dbnameconflict    int
    declare @max_rowlen        int
    
    /* this will make sure that all rows are sent even if
    ** the client "set rowcount" is differect
    */

    set rowcount 0


    if @table_qualifier is not null
    begin
        if db_name() != @table_qualifier
        begin
           SELECT @dbnameconflict = 1 
        end
    end

    SELECT @checktemptable = charindex('#',@table_name)
    /*
    **  if its a #temp table, assign @table_qualifier to the
    **  the temp db assigned to the user
    */

    if @checktemptable = 1
    begin
        SELECT @table_qualifier = db_name(@@tempdbid)
    end
    
    if @table_owner is null
    begin       /* If unqualified table name */
        SELECT @full_table_name = @table_qualifier + '..' + @table_name
        SELECT @table_owner = '%'
    end
    else
    begin       /* Qualified table name */
        SELECT @full_table_name = @table_qualifier + '.' + @table_owner + '.' + @table_name
    end

    SELECT @table_id=object_id(@full_table_name) 
    if @checktemptable = 1 OR @dbnameconflict = 1
    begin
        declare @cmd varchar(1500)
        SELECT @cmd = 'SELECT @sysstat2 = (sysstat2 & 57344) FROM '+@table_qualifier+'..sysobjects WHERE id = @table_id'
        execute(@cmd)        
        SELECT @cmd = 'SELECT @max_rowlen = maxlen FROM ' + @table_qualifier + '..sysindexes  WHERE id = @table_id AND indid in (0,1)'
        execute(@cmd)
    end
    else
    begin
        SELECT @sysstat2 = (sysstat2 & 57344) FROM sysobjects WHERE id = @table_id
        SELECT @max_rowlen = maxlen FROM sysindexes  WHERE id = @table_id AND indid in (0,1)
    end

    SELECT @allow_wide_dol = CASE WHEN ((status4 & 524288) != 0) THEN 1 ELSE 0 END FROM master.dbo.sysdatabases WHERE dbid = DB_ID(@table_qualifier)

    if ( @sysstat2 = 8192 OR @sysstat2 = 0)
    begin
    /* Lock scheme is Allpages */
    SELECT @table_lock_scheme = 0
    end
    if ( @sysstat2 = 16384 OR @sysstat2 = 32768)
    begin
    /* Lock scheme is Data only */
       SELECT @table_lock_scheme = 1
    end
    
    

    if (@table_id != 0)
    begin 
        if @checktemptable = 1 OR @dbnameconflict = 1
        begin
        SELECT @cmd = 'SELECT count(*),@table_qualifier FROM '+@table_qualifier+'..syscolumns WHERE id=@table_id '
        SELECT @cmd = @cmd + ' SELECT 
                  COLID=colid,
                  COLUMN_NAME=name, 
                  DATA_TYPE=(case when type=189 then 187
                        when type=190 then 188
                        else
                            type
                        end),
                  USERTYPE=usertype,
                  COLUMN_SIZE=length,
                  PRECISION=isnull(prec,0),
                  SCALE=isnull(scale,0),
                  NULLABLE=convert(bit, (status & 8)),
                  COLUMN_DEF=(SELECT text FROM syscomments WHERE id=c.cdefault),
                  IDENTITY_COL=convert(bit, (status & 0x80)),
                  TABLE_LOCK_SCHEME=@table_lock_scheme,
                  PAGESIZE=@@maxpagesize,
                  ALLOW_WIDE_DOL=@allow_wide_dol
                  ,
                  MAX_ROWLEN = @max_rowlen,
                  COL_OFFSET = offset,
                  TRUNCATE_VARBINARY_ZEROS = case when (status2 & 2097152) > 0 then 0
                      else 1
                  end,
                  IS_INROWLOB = case when (status2 & 262144) > 0 then 1
                  else 0
                  end,
                  INROWLOB_LEN = inrowlen
        FROM '+@table_qualifier+'..syscolumns c 
        WHERE id=@table_id
        ORDER BY colid'
        execute(@cmd)
        end
        else
        begin
        SELECT count(*),@table_qualifier FROM syscolumns WHERE id=@table_id
        SELECT 
                  COLID=colid,
                  COLUMN_NAME=name, 
                  DATA_TYPE=(case when type=189 then 187
                        when type=190 then 188
                        else
                            type
                        end),
                  USERTYPE=usertype,
                  COLUMN_SIZE=length,
                  'PRECISION'=isnull(prec,0),
                  SCALE=isnull(scale,0),
                  NULLABLE=convert(bit, (status & 8)),
                  COLUMN_DEF=(SELECT text FROM syscomments WHERE id=c.cdefault),
                  IDENTITY_COL=convert(bit, (status & 0x80)),
                  TABLE_LOCK_SCHEME=@table_lock_scheme,
                  PAGESIZE=@@maxpagesize,
                  ALLOW_WIDE_DOL=@allow_wide_dol
                  ,
                  MAX_ROWLEN = @max_rowlen,
                  COL_OFFSET = offset,
                  TRUNCATE_VARBINARY_ZEROS = case when (status2 & 2097152) > 0 then 0
                        else 1
                        end,
                  IS_INROWLOB = case when (status2 & 262144) > 0 then 1
                  else 0
                  end,
                  INROWLOB_LEN = inrowlen
        FROM syscolumns c 
        WHERE id=@table_id
        ORDER BY colid
        end
    end
    return(0)
go
exec sp_procxmode 'sp_drv_bcpmetadata', 'anymode'
go
grant execute on sp_drv_bcpmetadata to public
go

dump transaction master with truncate_only
go

dump transaction sybsystemprocs with truncate_only
go
use sybsystemprocs
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_locator_to_text')
begin
      drop procedure sp_drv_locator_to_text
end
go
CREATE PROCEDURE sp_drv_locator_to_text(@locator TEXT_LOCATOR) AS BEGIN SELECT return_lob(TEXT,@locator) END
go
exec sp_procxmode 'sp_drv_locator_to_text', 'anymode'
go
grant execute on sp_drv_locator_to_text to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_locator_to_unitext')
begin
      drop procedure sp_drv_locator_to_unitext
end
go
CREATE PROCEDURE sp_drv_locator_to_unitext(@locator UNITEXT_LOCATOR) AS BEGIN SELECT return_lob(UNITEXT,@locator) END
go
exec sp_procxmode 'sp_drv_locator_to_unitext', 'anymode'
go
grant execute on sp_drv_locator_to_unitext to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_locator_to_image')
begin
      drop procedure sp_drv_locator_to_image
end
go
CREATE PROCEDURE sp_drv_locator_to_image(@locator IMAGE_LOCATOR) AS BEGIN SELECT return_lob(IMAGE,@locator) END
go
exec sp_procxmode 'sp_drv_locator_to_image', 'anymode'
go
grant execute on sp_drv_locator_to_image to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_image_locator_valid')
begin
      drop procedure sp_drv_image_locator_valid
end
go
CREATE PROCEDURE sp_drv_image_locator_valid(@locator IMAGE_LOCATOR, @valid BIT OUTPUT) AS BEGIN SELECT @valid = locator_valid(@locator) END
go
exec sp_procxmode 'sp_drv_image_locator_valid', 'anymode'
go
grant execute on sp_drv_image_locator_valid to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_locator_valid')
begin
      drop procedure sp_drv_text_locator_valid
end
go
CREATE PROCEDURE sp_drv_text_locator_valid(@locator TEXT_LOCATOR, @valid BIT OUTPUT) AS BEGIN SELECT @valid = locator_valid(@locator) END
go
exec sp_procxmode 'sp_drv_text_locator_valid', 'anymode'
go
grant execute on sp_drv_text_locator_valid to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_locator_valid')
begin
      drop procedure sp_drv_unitext_locator_valid
end
go
CREATE PROCEDURE sp_drv_unitext_locator_valid(@locator UNITEXT_LOCATOR, @valid BIT OUTPUT) AS BEGIN SELECT @valid = locator_valid(@locator) END
go
exec sp_procxmode 'sp_drv_unitext_locator_valid', 'anymode'
go
grant execute on sp_drv_unitext_locator_valid to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_image_locator_bytelength')
begin
      drop procedure sp_drv_image_locator_bytelength
end
go
CREATE PROCEDURE sp_drv_image_locator_bytelength(@locator IMAGE_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = datalength(@locator) END
go
exec sp_procxmode 'sp_drv_image_locator_bytelength', 'anymode'
go
grant execute on sp_drv_image_locator_bytelength to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_locator_bytelength')
begin
      drop procedure sp_drv_text_locator_bytelength
end
go
CREATE PROCEDURE sp_drv_text_locator_bytelength(@locator TEXT_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = datalength(@locator) END
go
exec sp_procxmode 'sp_drv_text_locator_bytelength', 'anymode'
go
grant execute on sp_drv_text_locator_bytelength to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_locator_bytelength')
begin
      drop procedure sp_drv_unitext_locator_bytelength
end
go
CREATE PROCEDURE sp_drv_unitext_locator_bytelength(@locator UNITEXT_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = datalength(@locator) END
go
exec sp_procxmode 'sp_drv_unitext_locator_bytelength', 'anymode'
go
grant execute on sp_drv_unitext_locator_bytelength to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_locator_charlength')
begin
      drop procedure sp_drv_text_locator_charlength
end
go
CREATE PROCEDURE sp_drv_text_locator_charlength(@locator TEXT_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = char_length(@locator) END
go
exec sp_procxmode 'sp_drv_text_locator_charlength', 'anymode'
go
grant execute on sp_drv_text_locator_charlength to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_locator_charlength')
begin
      drop procedure sp_drv_unitext_locator_charlength
end
go
CREATE PROCEDURE sp_drv_unitext_locator_charlength(@locator UNITEXT_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = char_length(@locator) END
go
exec sp_procxmode 'sp_drv_unitext_locator_charlength', 'anymode'
go
grant execute on sp_drv_unitext_locator_charlength to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_locator_charindex')
begin
      drop procedure sp_drv_text_locator_charindex
end
go
CREATE PROCEDURE sp_drv_text_locator_charindex(@search_locator TEXT_LOCATOR, @locator TEXT_LOCATOR, @start INT=1, @index INT OUTPUT) AS BEGIN SELECT @index = charindex(@search_locator, @locator, @start) END
go
exec sp_procxmode 'sp_drv_text_locator_charindex', 'anymode'
go
grant execute on sp_drv_text_locator_charindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_locator_charindex')
begin
      drop procedure sp_drv_unitext_locator_charindex
end
go
CREATE PROCEDURE sp_drv_unitext_locator_charindex(@search_locator UNITEXT_LOCATOR, @locator UNITEXT_LOCATOR, @start INT=1, @index INT OUTPUT) AS BEGIN SELECT @index = charindex(@search_locator, @locator, @start) END
go
exec sp_procxmode 'sp_drv_unitext_locator_charindex', 'anymode'
go
grant execute on sp_drv_unitext_locator_charindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_image_locator_charindex')
begin
      drop procedure sp_drv_image_locator_charindex
end
go
CREATE PROCEDURE sp_drv_image_locator_charindex(@sequence_locator  IMAGE_LOCATOR, @locator IMAGE_LOCATOR, @start INT=1, @index INT OUTPUT) AS BEGIN SELECT @index = charindex(@sequence_locator, @locator, @start) END
go
exec sp_procxmode 'sp_drv_image_locator_charindex', 'anymode'
go
grant execute on sp_drv_image_locator_charindex to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_varchar_charindex')
begin
      drop procedure sp_drv_varchar_charindex
end
go
CREATE PROCEDURE sp_drv_varchar_charindex(@search_string VARCHAR(16384), @locator TEXT_LOCATOR, @start INT=1, @index INT OUTPUT) AS BEGIN 
SELECT @index = charindex(@search_string, @locator, @start) 
END
go
exec sp_procxmode 'sp_drv_varchar_charindex', 'anymode'
go
grant execute on sp_drv_varchar_charindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_univarchar_charindex')
begin
      drop procedure sp_drv_univarchar_charindex
end
go
CREATE PROCEDURE sp_drv_univarchar_charindex(@search_string UNIVARCHAR(8192), @locator UNITEXT_LOCATOR, @start INT=1, @index INT OUTPUT) AS BEGIN 
SELECT @index = charindex(@search_string, @locator, @start) 
END
go
exec sp_procxmode 'sp_drv_univarchar_charindex', 'anymode'
go
grant execute on sp_drv_univarchar_charindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_varbinary_charindex')
begin
      drop procedure sp_drv_varbinary_charindex
end
go
CREATE PROCEDURE sp_drv_varbinary_charindex(@byte_sequence VARBINARY(16384), @locator IMAGE_LOCATOR, @start INT=1, @index INT OUTPUT) AS BEGIN 
SELECT @index = charindex(@byte_sequence, @locator, @start) 
END
go
exec sp_procxmode 'sp_drv_varbinary_charindex', 'anymode'
go
grant execute on sp_drv_varbinary_charindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_locator_patindex')
begin
      drop procedure sp_drv_text_locator_patindex
end
go
CREATE PROCEDURE sp_drv_text_locator_patindex(@SubStr VARCHAR(16384), @locator TEXT_LOCATOR, @index INT OUTPUT) AS BEGIN 
SELECT @index = patindex(@SubStr, @locator) 
END
go
exec sp_procxmode 'sp_drv_text_locator_patindex', 'anymode'
go
grant execute on sp_drv_text_locator_patindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_locator_patindex')
begin
      drop procedure sp_drv_unitext_locator_patindex
end
go
CREATE PROCEDURE sp_drv_unitext_locator_patindex(@SubStr UNIVARCHAR(8192), @locator UNITEXT_LOCATOR, @index INT OUTPUT) AS BEGIN 
SELECT @index = patindex(@SubStr, @locator) 
END
go
exec sp_procxmode 'sp_drv_unitext_locator_patindex', 'anymode'
go
grant execute on sp_drv_unitext_locator_patindex to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_setdata')
begin
      drop procedure sp_drv_unitext_setdata
end
go
CREATE PROCEDURE sp_drv_unitext_setdata(@locator UNITEXT_LOCATOR, @offset INT, @new_data UNITEXT, @data_length INT OUTPUT) AS BEGIN 
SELECT @data_length = setdata(@locator, @offset, @new_data) 
END
go
exec sp_procxmode 'sp_drv_unitext_setdata', 'anymode'
go
grant execute on sp_drv_unitext_setdata to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_setdata')
begin
      drop procedure sp_drv_text_setdata
end
go
CREATE PROCEDURE sp_drv_text_setdata(@locator TEXT_LOCATOR, @offset INT, @new_data TEXT, @data_length INT OUTPUT) AS BEGIN 
SELECT @data_length = setdata(@locator, @offset, @new_data) 
END
go
exec sp_procxmode 'sp_drv_text_setdata', 'anymode'
go
grant execute on sp_drv_text_setdata to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_image_setdata')
begin
      drop procedure sp_drv_image_setdata
end
go
CREATE PROCEDURE sp_drv_image_setdata(@locator IMAGE_LOCATOR, @offset INT, @new_data IMAGE, @data_length INT OUTPUT) AS BEGIN 
SELECT @data_length = setdata(@locator, @offset, @new_data) 
END
go
exec sp_procxmode 'sp_drv_image_setdata', 'anymode'
go
grant execute on sp_drv_image_setdata to public
go



if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_locator_setdata')
begin
      drop procedure sp_drv_unitext_locator_setdata
end
go
CREATE PROCEDURE sp_drv_unitext_locator_setdata(@locator UNITEXT_LOCATOR, @offset INT, @new_data_locator UNITEXT_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = setdata(@locator, @offset, @new_data_locator) END
go
exec sp_procxmode 'sp_drv_unitext_locator_setdata', 'anymode'
go
grant execute on sp_drv_unitext_locator_setdata to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_locator_setdata')
begin
      drop procedure sp_drv_text_locator_setdata
end
go
CREATE PROCEDURE sp_drv_text_locator_setdata(@locator TEXT_LOCATOR, @offset INT, @new_data_locator TEXT_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = setdata(@locator, @offset, @new_data_locator) END
go
exec sp_procxmode 'sp_drv_text_locator_setdata', 'anymode'
go
grant execute on sp_drv_text_locator_setdata to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_image_locator_setdata')
begin
      drop procedure sp_drv_image_locator_setdata
end
go
CREATE PROCEDURE sp_drv_image_locator_setdata(@locator IMAGE_LOCATOR, @offset INT, @new_data_locator IMAGE_LOCATOR, @data_length INT OUTPUT) AS BEGIN SELECT @data_length = setdata(@locator, @offset, @new_data_locator) END
go
exec sp_procxmode 'sp_drv_image_locator_setdata', 'anymode'
go
grant execute on sp_drv_image_locator_setdata to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_unitext_substring')
begin
      drop procedure sp_drv_unitext_substring
end
go
CREATE PROCEDURE sp_drv_unitext_substring(@locator UNITEXT_LOCATOR, @start INT, @length INT) AS BEGIN 
SELECT return_lob(UNITEXT, substring(@locator, @start, @length))
END
go
exec sp_procxmode 'sp_drv_unitext_substring', 'anymode'
go
grant execute on sp_drv_unitext_substring to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_text_substring')
begin
      drop procedure sp_drv_text_substring
end
go
CREATE PROCEDURE sp_drv_text_substring(@locator TEXT_LOCATOR, @start INT, @length INT) AS BEGIN 
SELECT return_lob(TEXT, substring(@locator, @start, @length))
END
go
exec sp_procxmode 'sp_drv_text_substring', 'anymode'
go
grant execute on sp_drv_text_substring to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_image_substring')
begin
      drop procedure sp_drv_image_substring
end
go
CREATE PROCEDURE sp_drv_image_substring(@locator IMAGE_LOCATOR, @start INT, @length INT) AS BEGIN 
SELECT return_lob(IMAGE, substring(@locator, @start, @length))
END
go
exec sp_procxmode 'sp_drv_image_substring', 'anymode'
go
grant execute on sp_drv_image_substring to public
go


if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_create_text_locator')
begin
      drop procedure sp_drv_create_text_locator
end
go
CREATE PROCEDURE sp_drv_create_text_locator(@value TEXT = NULL) AS BEGIN SELECT CREATE_LOCATOR(TEXT_LOCATOR, @value) END
go
exec sp_procxmode 'sp_drv_create_text_locator', 'anymode'
go
grant execute on sp_drv_create_text_locator to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_create_unitext_locator')
begin
      drop procedure sp_drv_create_unitext_locator
end
go
CREATE PROCEDURE sp_drv_create_unitext_locator(@value UNITEXT = NULL) AS BEGIN SELECT CREATE_LOCATOR(UNITEXT_LOCATOR, @value) END
go
exec sp_procxmode 'sp_drv_create_unitext_locator', 'anymode'
go
grant execute on sp_drv_create_unitext_locator to public
go

if exists (SELECT *
      from sysobjects
            where sysstat & 7 = 4
                  and name = 'sp_drv_create_image_locator')
begin
      drop procedure sp_drv_create_image_locator
end
go
CREATE PROCEDURE sp_drv_create_image_locator(@value IMAGE = NULL) AS BEGIN SELECT CREATE_LOCATOR(IMAGE_LOCATOR, @value) END
go
exec sp_procxmode 'sp_drv_create_image_locator', 'anymode'
go
grant execute on sp_drv_create_image_locator to public
go

dump transaction master with truncate_only
go

dump transaction sybsystemprocs with truncate_only
go
