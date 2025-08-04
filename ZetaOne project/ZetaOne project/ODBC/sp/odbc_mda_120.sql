/* Master only */
/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */
/*
**  ODBC_INSTALL
**  This file contains the metadata Stored Procedures used by the ODBC drivers.
**
*/

/*
** Stored procedures created:
**
** Name                          	Default Location	Comments
** --------------------------------------------------------------------------------------------------
** 1>  sp_odbc_server_info		sybsystemprocs
** 2>  sp_odbc_databases		sybsystemprocs
** 3>  sp_odbc_columns			sybsystemprocs
** 4>  sp_odbc_datatype_info		sybsystemprocs
** 5>  sp_odbc_getversioncolumns	sybsystemprocs		
** 6>  sp_odbc_getcolumnprivileges	sybsystemprocs
** 7>  sp_odbc_tables			sybsystemprocs
** 8>  sp_odbc_gettableprivileges	sybsystemprocs
** 9>  sp_odbc_getindexinfo		sybsystemprocs
** 10> sp_odbc_primarykey		sybsystemprocs
** 11> sp_odbc_fkeys			sybsystemprocs
** 12> sp_odbc_stored_procedures	sybsystemprocs
** 13> sp_odbc_getprocedurecolumns	sybsystemprocs
** 14> sp_odbc_computeprivs		sybsystemprocs	added to support ,
**								sp_odbc_gettableprivileges
**								sp_odbc_getcolumnprivileges
** 15> sp_version			sybsystemprocs
** 16> sp_drv_bcpmetadata		sybsystemprocs		for BulkInsert Support
*/
set flushmessage on
go

print ""
go

declare @version_string varchar(255) 
select @version_string = '15.7.0.80.1008/'+ 'Fri Aug 26 UTC 01:00:28 2011'
print "ODBC - Build Version : %1!", @version_string 
declare @retval int
exec @retval = sp_version 'ODBC MDA Scripts', NULL, @version_string, 'start'
if (@retval != 0) select syb_quit()
go


use sybsystemprocs
go

if exists (select * from sysobjects where name = 'sp_odbc_computeprivs')
    begin
        drop procedure sp_odbc_computeprivs
    end
go

/*
** Results Table needs to be created so that sp_odbc_computeprivs has a temp
** table to reference when the procedure is compiled.  Otherwise, the calling
** stored procedure will create the temp table for sp_odbc_computeprivs.
*/
create table #results_table
        (table_qualifier        varchar (32),
         table_owner            varchar (32),
         table_name             varchar (32),
         column_name            varchar (32) NULL,
         grantor                varchar (32),
         grantee                varchar (32),
         privilege              varchar (32),
         is_grantable           varchar (3))
go

create procedure sp_odbc_computeprivs (
                        @table_name             varchar(32),
                        @table_owner            varchar(32),
                        @table_qualifier        varchar(32),
                        @column_name            varchar(32),
                        @calledfrom_colpriv     tinyint,
                        @tab_id                 int)

AS

/* Don't delete the following line. It is the checkpoint for sed */
/* Server dependent stored procedure add here ad ADDPOINT_COMPUTE_PRIVS */

    declare @low 		int		/* range of userids to check */
    declare @high 		int
    declare @max_uid		smallint        /* max uid allowed for a user */
    
    declare @grantor_name       varchar (32)    /* the ascii name of grantor.
                                                   used for output */
    declare @grantee_name       varchar (32)    /* the ascii name of grantee.
                                                   used for output */
    declare @col_count          smallint        /* number of columns in
                                                   @table_name */
    declare @grantee            int             /* id of the grantee */
    declare @action             smallint        /* action refers to select,
                                                   update...*/
    declare @columns            varbinary (133) /* bit map of column
                                                   privileges */
    declare @protecttype        tinyint         /* grant/revoke or grant with
                                                   grant option */
    declare @grantor            int             /* id of the grantor of the
                                                   privilege */
    declare @grp_id             int             /* the group a user belongs
                                                   to */
    declare @grant_type         tinyint         /* used as a constant */
    declare @revoke_type        tinyint         /* used as a constant */
    declare @select_action      smallint        /* used as a constant */
    declare @update_action      smallint        /* used as a constant */
    declare @reference_action   smallint        /* used as a constant */
    declare @insert_action      smallint        /* used as a constant */
    declare @delete_action      smallint        /* used as a constant */
    declare @public_select      varbinary (133) /* stores select column bit map
                                                   for public */
    declare @public_reference   varbinary (133) /* stores reference column bit
                                                   map for public */
    declare @public_update      varbinary (133) /* stores update column bit map
                                                   for public */
    declare @public_insert      tinyint         /* stores if insert has been
                                                   granted to public */
    declare @public_delete      tinyint         /* store if delete has been
                                                   granted to public */
    declare @grp_select         varbinary (133) /* stores select column bit map
                                                   for group */
    declare @grp_update         varbinary (133) /* stores update column bit map
                                                   for group */
    declare @grp_reference      varbinary (133) /* stores reference column bit
                                                   map for group */
    declare @grp_delete         tinyint         /* if group hs been granted
                                                   delete privilege */
    declare @grp_insert         tinyint         /* if group has been granted
                                                   insert privilege */
    declare @inherit_select     varbinary (133) /* stores select column bit map
                                                   for inherited privs*/
    declare @inherit_update     varbinary (133) /* stores update column bit map
                                                   for inherited privs */
    declare @inherit_reference  varbinary (133) /* stores reference column bit
                                                   map for inherited privs */
    declare @inherit_insert     tinyint         /* inherited insert priv */
    declare @inherit_delete     tinyint         /* inherited delete priv */
    declare @select_go          varbinary (133) /* user column bit map of
                                                   select with grant */
    declare @update_go          varbinary (133) /* user column bit map of
                                                   update with grant */
    declare @reference_go       varbinary (133) /* user column bitmap of
                                                   reference with grant */
    declare @insert_go          tinyint         /* user insert priv with
                                                   grant option */
    declare @delete_go          tinyint         /* user delete priv with grant
                                                   option  */
    declare @prev_grantor       int             /* used to detect if the
                                                   grantor has changed between
                                                   two consecutive tuples */
    declare @col_pos            smallint        /* col_pos of the column we are
                                                   interested in. It is used to
                                                   find the col-bit in the
                                                   bitmap */
    declare @owner_id           int             /* id of the owner of the
                                                   table */
    declare @dbid               smallint        /* dbid for the table */
    declare @grantable          varchar (3)     /* 'YES' or 'NO' if the
                                                   privilege is grantable or
                                                   not */
    declare @is_printable       tinyint         /* 1, if the privilege info is
                                                   to be outputted */
    declare @startedInTransaction bit
    if (@@trancount > 0)
  	select @startedInTransaction = 1
    else
        select @startedInTransaction = 0
                                                       

    if (@startedInTransaction = 1)
	save transaction odbc_keep_temptable_tx    

/* 
** Initialize all constants to be used in this procedure
*/

    select @grant_type = 1

    select @revoke_type = 2
   
    select @select_action = 193

    select @reference_action = 151

    select @update_action = 197

    select @delete_action = 196

    select @insert_action = 195

    select @max_uid = 16383

    select @low = -32768, @high = 32767
    
/*
** compute the table owner id
*/

    select @owner_id = uid
    from   sysobjects
    where  id = @tab_id

/*
** create a temporary sysprotects table that only has grant/revoke tuples
** for the requested table. This is done as an optimization as the sysprotects
** table may need to be traversed several times
*/

    create table #sysprotects
        (uid            int,
         action         smallint,
         protecttype    tinyint,
         columns        varbinary (133) NULL,
         grantor        int)

/*
** This table contains all the groups including PUBLIC that users, who
** have been granted privilege on this table, belong to. Also it includes
** groups that have been explicitly granted privileges on the table object
*/
    create table #useful_groups
        (grp_id         int)

/*
** create a table that contains the list of grantors for the object requested.
** We will do a cartesian product of this table with sysusers in the
** current database to capture all grantor/grantee tuples
*/

    create table #distinct_grantors
        (grantor        int)

/*
** We need to create a table which will contain a row for every object
** privilege to be returned to the client.  
*/

    create table #column_privileges 
        (grantee_gid    int,
         grantor        int,
         grantee        int,
         insertpriv     tinyint,
         insert_go      tinyint NULL,
         deletepriv     tinyint,
         delete_go      tinyint NULL,
         selectpriv     varbinary (133) NULL,
         select_go      varbinary (133) NULL,
         updatepriv     varbinary (133) NULL,
         update_go      varbinary (133) NULL,
         referencepriv  varbinary (133) NULL,
         reference_go   varbinary (133) NULL)

/*
** this cursor scans the distinct grantor, group_id pairs
*/
    declare grp_cursor cursor for
        select distinct grp_id, grantor 
        from #useful_groups, #distinct_grantors
        order by grantor

/* 
** this cursor scans all the protection tuples that represent
** grant/revokes to users only
*/
    declare user_protect cursor for
        select uid, action, protecttype, columns, grantor
        from   #sysprotects
        where  (uid != 0) and
              (uid <= @max_uid)
--               ((uid >= @@minuserid and uid < @@mingroupid) or 
--               (uid > @@maxgroupid and uid <= @@maxuserid)) 


/*
** this cursor is used to scan #column_privileges table to output results
*/
    declare col_priv_cursor cursor for
          select grantor, grantee, insertpriv, insert_go, deletepriv,
              delete_go, selectpriv, select_go, updatepriv, update_go,
              referencepriv, reference_go
          from #column_privileges



/*
** column count is needed for privilege bit-map manipulation
*/
    select @col_count = count (*) 
    from   syscolumns
    where  id = @tab_id


/* 
** populate the temporary sysprotects table #sysprotects
*/

        insert into #sysprotects 
                select uid, action, protecttype, columns, grantor
                from sysprotects
                where (id = @tab_id)               and
                      ((action = @select_action)   or
                      (action = @update_action)    or
                      (action = @reference_action) or
                      (action = @insert_action)    or
                      (action = @delete_action))

/* 
** insert privilege tuples for the table owner. There is no explicit grants
** of these privileges to the owner. So these tuples are not there in
** sysprotects table
*/

if not exists (select * from #sysprotects where (action = @select_action) and
                (protecttype = @revoke_type) and (uid = @owner_id))
begin
        insert into #sysprotects
             values (@owner_id, @select_action, 0, 0x01, @owner_id)
end

if not exists (select * from #sysprotects where (action = @update_action) and
                (protecttype = @revoke_type) and (uid = @owner_id))
begin
        insert into #sysprotects
             values (@owner_id, @update_action, 0, 0x01, @owner_id)
end

if not exists (select * from #sysprotects where (action = @reference_action) and
                (protecttype = @revoke_type) and (uid = @owner_id))
begin
        insert into #sysprotects
             values (@owner_id, @reference_action, 0, 0x01, @owner_id)
end

if not exists (select * from #sysprotects where (action = @insert_action) and
                (protecttype = @revoke_type) and (uid = @owner_id))
begin
        insert into #sysprotects
             values (@owner_id, @insert_action, 0, NULL, @owner_id)
end

if not exists (select * from #sysprotects where (action = @delete_action) and
                (protecttype = @revoke_type) and (uid = @owner_id))
begin
        insert into #sysprotects
             values (@owner_id, @delete_action, 0, NULL, @owner_id)
end


/* 
** populate the #distinct_grantors table with all grantors that have granted
** the privilege to users or to gid or to public on the table_name
*/

    insert into #distinct_grantors 
          select distinct grantor from #sysprotects

/* 
** Populate the #column_privilegs table as a cartesian product of the table
** #distinct_grantors and all the users, other than groups, in the current
** database
*/


    insert into #column_privileges
          select gid, g.grantor, su.uid, 0, 0, 0, 0, 0x00, 0x00, 0x00, 0x00,
              0x00, 0x00
          from sysusers su, #distinct_grantors g
        where  (su.uid != 0) and
                (su.uid <= @max_uid)
--               ((su.uid >= @@minuserid and su.uid < @@mingroupid) or
--               (su.uid > @@maxgroupid and su.uid <= @@maxuserid)) 

/*
** populate #useful_groups with only those groups whose members have been
** granted/revoked privileges on the @tab_id in the current database. It also
** contains those groups that have been granted/revoked privileges explicitly
*/

    insert into #useful_groups
        select distinct gid
        from   sysusers su, #sysprotects sp
        where  (su.uid = sp.uid) 


    open grp_cursor

    fetch grp_cursor into @grp_id, @grantor

    /* 
    ** This loop computes all the inherited privilegs of users due
    ** their membership in a group
    */

    while (@@sqlstatus != 2)
   
    begin

         /* 
         ** initialize variables 
         */
         select @public_select = 0x00
         select @public_update = 0x00
         select @public_reference = 0x00
         select @public_delete = 0
         select @public_insert = 0


         /* get the select privileges granted to PUBLIC */

         if (exists (select * from #sysprotects 
                     where (grantor = @grantor) and 
                           (uid = 0) and
                           (action = @select_action)))
         begin
              /* note there can't be any revoke row for PUBLIC */
              select @public_select = columns
              from #sysprotects
              where (grantor = @grantor) and 
                    (uid = 0) and
                    (action = @select_action)
         end


         /* get the update privilege granted to public */
         if (exists (select * from #sysprotects 
                     where (grantor = @grantor) and 
                           (uid = 0) and
                           (action = @update_action)))
         begin
              /* note there can't be any revoke row for PUBLIC */
              select @public_update = columns
              from #sysprotects
              where (grantor = @grantor) and 
                    (uid = 0) and
                    (action = @update_action)
         end

         /* get the reference privileges granted to public */
         if (exists (select * from #sysprotects 
                     where (grantor = @grantor) and 
                           (uid = 0) and
                           (action = @reference_action)))
         begin
              /* note there can't be any revoke row for PUBLIC */
              select @public_reference = columns
              from #sysprotects
              where (grantor = @grantor) and 
                    (uid = 0) and
                    (action = @reference_action)
         end


         /* get the delete privilege granted to public */
         if (exists (select * from #sysprotects 
                     where (grantor = @grantor) and 
                           (uid = 0) and
                           (action = @delete_action)))
         begin
              /* note there can't be any revoke row for PUBLIC */
              select @public_delete = 1
         end

         /* get the insert privileges granted to public */
         if (exists (select * from #sysprotects 
                     where (grantor = @grantor) and 
                           (uid = 0) and
                           (action = @insert_action)))
         begin
              /* note there can't be any revoke row for PUBLIC */
              select @public_insert = 1
         end


         /*
         ** initialize group privileges 
         */

         select @grp_select = 0x00
         select @grp_update = 0x00
         select @grp_reference = 0x00
         select @grp_insert = 0
         select @grp_delete = 0

         /* 
         ** if the group id is other than PUBLIC, we need to find the grants to
         ** the group also 
         */

         if (@grp_id <> 0)
         begin
                /* find select privilege granted to group */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @grant_type) and
                                  (action = @select_action)))
                begin
                        select @grp_select = columns
                        from #sysprotects
                        where (grantor = @grantor) and 
                              (uid = @grp_id) and
                              (protecttype = @grant_type) and 
                              (action = @select_action)
                end

                /* find update privileges granted to group */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @grant_type) and
                                  (action = @update_action)))
                begin
                        select @grp_update = columns
                        from #sysprotects
                        where (grantor = @grantor) and 
                              (uid = @grp_id) and
                              (protecttype = @grant_type) and 
                              (action = @update_action)
                end

                /* find reference privileges granted to group */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @grant_type) and
                                  (action = @reference_action)))
                begin
                        select @grp_reference = columns
                        from #sysprotects
                        where (grantor = @grantor) and 
                              (uid = @grp_id) and
                              (protecttype = @grant_type) and 
                              (action = @reference_action)
                end

                /* find delete privileges granted to group */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @grant_type) and
                                  (action = @delete_action)))
                begin

                        select @grp_delete = 1
                end

                /* find insert privilege granted to group */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @grant_type) and
                                  (action = @insert_action)))
                begin

                        select @grp_insert = 1

                end

         end

         /* at this stage we have computed all the grants to PUBLIC as well as
         ** the group by a specific grantor that we are interested in. Now we
         ** will use this info to compute the overall inherited privileges by
         ** the users due to their membership to the group or to PUBLIC 
         */


         exec sybsystemprocs.dbo.syb_aux_privunion @public_select, @grp_select,
             @col_count, @inherit_select output
         exec sybsystemprocs.dbo.syb_aux_privunion @public_update, @grp_update, 
             @col_count, @inherit_update output
         exec sybsystemprocs.dbo.syb_aux_privunion @public_reference,
             @grp_reference, @col_count, @inherit_reference output

         select @inherit_insert = @public_insert + @grp_insert
         select @inherit_delete = @public_delete + @grp_delete

         /*
         ** initialize group privileges to store revokes
         */

         select @grp_select = 0x00
         select @grp_update = 0x00
         select @grp_reference = 0x00
         select @grp_insert = 0
         select @grp_delete = 0

         /* 
         ** now we need to find if there are any revokes on the group under
         ** consideration. We will subtract all privileges that are revoked
         ** from the group from the inherited privileges
         */

         if (@grp_id <> 0)
         begin
                /* check if there is a revoke row for select privilege*/
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @revoke_type) and
                                  (action = @select_action)))
                begin
                        select @grp_select = columns
                        from #sysprotects
                        where (grantor = @grantor) and 
                              (uid = @grp_id) and
                              (protecttype = @revoke_type) and 
                              (action = @select_action)
                end

                /* check if there is a revoke row for update privileges */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @revoke_type) and
                                  (action = @update_action)))
                begin
                        select @grp_update = columns
                        from #sysprotects
                        where (grantor = @grantor) and 
                              (uid = @grp_id) and
                              (protecttype = @revoke_type) and 
                              (action = @update_action)
                end

                /* check if there is a revoke row for reference privilege */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @revoke_type) and
                                  (action = @reference_action)))
                begin
                        select @grp_reference = columns
                        from #sysprotects
                        where (grantor = @grantor) and 
                              (uid = @grp_id) and
                              (protecttype = @revoke_type) and 
                              (action = @reference_action)
                end

                /* check if there is a revoke row for delete privilege */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @revoke_type) and
                                  (action = @delete_action)))
                begin
                        select @grp_delete = 1
                end

                /* check if there is a revoke row for insert privilege */
                if (exists (select * from #sysprotects 
                            where (grantor = @grantor) and 
                                  (uid = @grp_id) and
                                  (protecttype = @revoke_type) and
                                  (action = @insert_action)))
                begin
                        select @grp_insert = 1

                end


                /* 
                ** now subtract the revoked privileges from the group
                */

                exec sybsystemprocs.dbo.syb_aux_privexor @inherit_select,
                                                 @grp_select,
                                                 @col_count,
                                                 @inherit_select output

                exec sybsystemprocs.dbo.syb_aux_privexor @inherit_update,
                                                 @grp_update,
                                                 @col_count,
                                                 @inherit_update output

                exec sybsystemprocs.dbo.syb_aux_privexor @inherit_reference,
                                                 @grp_reference,
                                                 @col_count,
                                                 @inherit_reference output

                if (@grp_delete = 1)
                        select @inherit_delete = 0

                if (@grp_insert = 1)
                        select @inherit_insert = 0

         end

         /*
         ** now update all the tuples in #column_privileges table for this
         ** grantor and group id
         */

         update #column_privileges
         set
                insertpriv      = @inherit_insert,
                deletepriv      = @inherit_delete,
                selectpriv      = @inherit_select,
                updatepriv      = @inherit_update,
                referencepriv   = @inherit_reference

         where (grantor     = @grantor) and
               (grantee_gid = @grp_id)


         /*
         ** the following update updates the privileges for those users
         ** whose groups have not been explicitly granted privileges by the
         ** grantor. So they will all have all the privileges of the PUBLIC
         ** that were granted by the current grantor
         */

         select @prev_grantor = @grantor         
         fetch grp_cursor into @grp_id, @grantor

         if ((@prev_grantor <> @grantor) or (@@sqlstatus = 2))

         begin
         /* Either we are at the end of the fetch or we are switching to
         ** a different grantor. 
         */

               update #column_privileges 
               set
                        insertpriv      = @public_insert,
                        deletepriv      = @public_delete,
                        selectpriv      = @public_select,
                        updatepriv      = @public_update,
                        referencepriv   = @public_reference
                from #column_privileges cp
                where (cp.grantor = @prev_grantor) and
                      (not EXISTS (select * 
                                   from #useful_groups ug
                                   where ug.grp_id = cp.grantee_gid))

         end
    end


    close grp_cursor


    /* 
    ** At this stage, we have populated the #column_privileges table with
    ** all the inherited privileges
    */
    /*
    ** update #column_privileges to give all access to the table owner that way
    ** if there are any revoke rows in sysprotects, then the calculations will
    ** be done correctly.  There will be no revoke rows for table owner if
    ** privileges are revoked from a group that the table owner belongs to.
    */
    update #column_privileges
    set
        insertpriv      = 0x01, 
        deletepriv      = 0x01, 
        selectpriv      = 0x01,
        updatepriv      = 0x01,
        referencepriv   = 0x01

        where grantor = grantee
          and grantor = @owner_id

    
    /* 
    ** Now we will go through each user grant or revoke in table #sysprotects
    ** and update the privileges in #column_privileges table
    */
    open user_protect

    fetch user_protect into @grantee, @action, @protecttype, @columns, @grantor

    while (@@sqlstatus != 2)
    begin
        /*
        ** In this loop, we can find grant row, revoke row or grant with grant
        ** option row. We use protecttype to figure that. If it is grant, then
        ** the user specific privileges are added to the user's inherited
        ** privileges. If it is a revoke, then the revoked privileges are
        ** subtracted from the inherited privileges. If it is a grant with
        ** grant option, we just store it as is because privileges can
        ** only be granted with grant option to individual users
        */

        /* 
        ** for select action
        */
        if (@action = @select_action)
        begin
             /* get the inherited select privilege */
             select @inherit_select = selectpriv
             from   #column_privileges
             where  (grantee = @grantee) and
                    (grantor = @grantor)

             if (@protecttype = @grant_type)
             /* the grantee has a individual grant */
                exec sybsystemprocs.dbo.syb_aux_privunion @inherit_select,
                    @columns, @col_count, @inherit_select output

             else 
                if (@protecttype = @revoke_type)
                /* it is a revoke row */
                     exec sybsystemprocs.dbo.syb_aux_privexor @inherit_select,
                         @columns, @col_count, @inherit_select output

                else
                     /* it is a grant with grant option */

                     select @select_go = @columns

             /* modify the privileges for this user */

             if ((@protecttype = @revoke_type) or (@protecttype = @grant_type))
             begin
                  update #column_privileges
                  set selectpriv = @inherit_select
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
             else
             begin

                  update #column_privileges
                  set select_go = @select_go
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
        end

        /*
        ** update action
        */
        if (@action = @update_action)
        begin
             /* find out the inherited update privilege */
             select @inherit_update = updatepriv
             from   #column_privileges
             where  (grantee = @grantee) and
                    (grantor = @grantor)


             if (@protecttype = @grant_type)
             /* user has an individual grant */
                exec sybsystemprocs.dbo.syb_aux_privunion @inherit_update,
                    @columns, @col_count, @inherit_update output

             else 
                if (@protecttype = @revoke_type)
                     exec sybsystemprocs.dbo.syb_aux_privexor @inherit_update,
                         @columns, @col_count, @inherit_update output

                else
                     /* it is a grant with grant option */
                     select @update_go = @columns


             /* modify the privileges for this user */

             if ((@protecttype = @revoke_type) or (@protecttype = @grant_type))
             begin
                  update #column_privileges
                  set updatepriv = @inherit_update
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
             else
             begin
                  update #column_privileges
                  set update_go = @update_go
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
        end

        /* it is the reference privilege */
        if (@action = @reference_action)
        begin
             select @inherit_reference = referencepriv
             from   #column_privileges
             where  (grantee = @grantee) and
                    (grantor = @grantor)


             if (@protecttype = @grant_type)
             /* the grantee has a individual grant */
                exec sybsystemprocs.dbo.syb_aux_privunion @inherit_reference,
                    @columns, @col_count, @inherit_reference output

             else 
                if (@protecttype = @revoke_type)
                /* it is a revoke row */
                     exec sybsystemprocs.dbo.syb_aux_privexor
                        @inherit_reference, @columns, @col_count,
                        @inherit_reference output

                else
                     /* it is a grant with grant option */
                     select @reference_go = @columns


             /* modify the privileges for this user */

             if ((@protecttype = @revoke_type) or (@protecttype = @grant_type))
             begin
                  update #column_privileges
                  set referencepriv = @inherit_reference
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
             else
             begin
                  update #column_privileges
                  set reference_go = @reference_go
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end

        end

        /*
        ** insert action
        */

        if (@action = @insert_action)
        begin
             if (@protecttype = @grant_type)
                   select @inherit_insert = 1
             else
                 if (@protecttype = @revoke_type)
                      select @inherit_insert = 0
                 else
                      select @insert_go = 1

             
             /* modify the privileges for this user */

             if ((@protecttype = @revoke_type) or (@protecttype = @grant_type))
             begin
                  update #column_privileges
                  set insertpriv = @inherit_insert
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
             else
             begin
                  update #column_privileges
                  set insert_go = @insert_go
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end

        end

        /* 
        ** delete action
        */

        if (@action = @delete_action)
        begin
             if (@protecttype = @grant_type)
                   select @inherit_delete = 1
             else
                 if (@protecttype = @revoke_type)
                      select @inherit_delete = 0
                 else
                      select @delete_go = 1

             
             /* modify the privileges for this user */

             if ((@protecttype = @revoke_type) or (@protecttype = @grant_type))
             begin
                  update #column_privileges
                  set deletepriv = @inherit_delete
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end
             else
             begin
                  update #column_privileges
                  set delete_go = @delete_go
                  where (grantor = @grantor) and
                        (grantee = @grantee)
             end

        end

        fetch user_protect into @grantee, @action, @protecttype, @columns,
            @grantor
    end

    close user_protect

open col_priv_cursor
fetch col_priv_cursor into @grantor, @grantee, @inherit_insert, @insert_go,
                         @inherit_delete, @delete_go, @inherit_select,
                         @select_go, @inherit_update, @update_go,
                         @inherit_reference, @reference_go

while (@@sqlstatus != 2)
begin

      /* 
      ** name of the grantor
      */
      select @grantor_name = name 
      from   sysusers
      where  uid = @grantor


      /*
      ** name of the grantee
      */

      select @grantee_name = name
      from   sysusers
      where  uid = @grantee

      /* 
      ** At this point, we are either printing privilege information for a
      ** a specific column or for table_privileges
      */

            select @col_pos = 0

            if (@calledfrom_colpriv = 1)
            begin
            /* 
            ** find the column position
            */
                 select @col_pos = colid
                 from syscolumns
                 where (id = @tab_id) and
                       (name = @column_name)
            end

            /* 
            ** check for insert privileges
            */
            /* insert privilege is only a table privilege */
            if (@calledfrom_colpriv = 0)
            begin
                    exec sybsystemprocs.dbo.syb_aux_printprivs 
                        @calledfrom_colpriv, @col_pos, @inherit_insert,
                        @insert_go, 0x00, 0x00, 0, @grantable output,
                        @is_printable output

                    if (@is_printable = 1)
                    begin
                          insert into #results_table
                               values (@table_qualifier, @table_owner,
                                       @table_name, @column_name,
                                       @grantor_name, @grantee_name, 'INSERT',
                                       @grantable)
                    end
            end

            /* 
            ** check for delete privileges
            */

            if (@calledfrom_colpriv = 0)
            /* delete privilege need only be printed if called from
               sp_table_privileges */
            begin
                    exec sybsystemprocs.dbo.syb_aux_printprivs 
                         @calledfrom_colpriv, @col_pos, @inherit_delete,
                         @delete_go, 0x00, 0x00, 0, @grantable output,
                         @is_printable output

                    if (@is_printable = 1)
                    begin
                        insert into #results_table
                                values (@table_qualifier, @table_owner,
                                        @table_name, @column_name,
                                        @grantor_name, @grantee_name, 'DELETE',
                                        @grantable)
                    end
            end

            /* 
            ** check for select privileges
            */
            exec sybsystemprocs.dbo.syb_aux_printprivs 
                        @calledfrom_colpriv, @col_pos, 0, 0, @inherit_select,
                        @select_go, 1, @grantable output, @is_printable output


            if (@is_printable = 1)
            begin
                  insert into #results_table
                         values (@table_qualifier, @table_owner, @table_name,
                                 @column_name, @grantor_name, @grantee_name,
                                 'SELECT', @grantable)
            end
            /* 
            ** check for update privileges
            */
            exec sybsystemprocs.dbo.syb_aux_printprivs 
                @calledfrom_colpriv, @col_pos, 0, 0, @inherit_update,
                @update_go, 1, @grantable output, @is_printable output

            if (@is_printable = 1)
            begin
                  insert into #results_table
                        values (@table_qualifier, @table_owner, @table_name,
                                @column_name, @grantor_name, @grantee_name,
                                'UPDATE', @grantable)
            end
            /*
            ** check for reference privs
            */
            exec sybsystemprocs.dbo.syb_aux_printprivs 
                @calledfrom_colpriv, @col_pos, 0, 0, @inherit_reference,
                @reference_go, 1, @grantable output, @is_printable output

            if (@is_printable = 1)
            begin
                insert into #results_table
                        values (@table_qualifier, @table_owner, @table_name,
                                @column_name, @grantor_name, @grantee_name,
                                'REFERENCE', @grantable)
            end



      fetch col_priv_cursor into @grantor, @grantee, @inherit_insert,
          @insert_go, @inherit_delete, @delete_go, @inherit_select, @select_go,
          @inherit_update, @update_go, @inherit_reference, @reference_go
end

close col_priv_cursor

    drop table #column_privileges
    drop table #distinct_grantors
    drop table #sysprotects
    drop table #useful_groups
    
    if (@startedInTransaction = 1)
	rollback transaction odbc_keep_temptable_tx    


go

/*
** Drop temp table used for creation of sp_odbc_computeprivs
*/
drop table #results_table
go

exec sp_procxmode 'sp_odbc_computeprivs', 'anymode'
go

grant execute on sp_odbc_computeprivs to public
go


if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_server_info')
begin
	drop procedure sp_odbc_server_info
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */

/*
** Messages for "sp_odbc_server_info"
**
** 18059, "Attribute id %1! is not supported."
*/

create procedure sp_odbc_server_info
@attribute_id int = NULL		/* optional attribute id */
as


set nocount on

/* If an attribute id was specified then just return the info for that
** attribute.
*/
if @attribute_id is not null
begin
	/* Verify that the attribute is valid. */
	if not exists ( select attribute_id 
		from sybsystemprocs.dbo.spt_server_info
			where attribute_id = @attribute_id )
	begin
		/*
		** 18059, "Attribute id %1! is not supported."
		*/
		raiserror 18059, @attribute_id
		return (1)
	end

	select * from sybsystemprocs.dbo.spt_server_info
		where attribute_id = @attribute_id
end

/* If no attribute was specified then return info for all supported
** attributes.
*/
else
begin
	select * from sybsystemprocs.dbo.spt_server_info
end

return (0)
go
exec sp_procxmode 'sp_odbc_server_info', 'anymode'
go
grant execute on sp_odbc_server_info to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go
if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_databases')
begin
	drop procedure sp_odbc_databases
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */

create procedure sp_odbc_databases
as

    declare @startedInTransaction bit
    if (@@trancount > 0)
  	select @startedInTransaction = 1
    else
        select @startedInTransaction = 0
                                                       


	if @@trancount = 0
	begin
		set chained off
	end

	set transaction isolation level 1

    if (@startedInTransaction = 1)
	save transaction odbc_keep_temptable_tx    


	/* Use temporary table to sum up database size w/o using group by */
	create table #databases (
				  database_name varchar(32),
				  size int)

	/* Insert row for each database */
	insert into #databases
		select
			name,
			(select sum(size) from master.dbo.sysusages
				where dbid = d.dbid)
		from master.dbo.sysdatabases d

	select
		 database_name,
				/* Convert from number of pages to K */
		 database_size = size * (@@pagesize / 1024),
		 remarks = convert(varchar(254),null)	/* Remarks are NULL */
	from #databases

    drop table #databases
    if (@startedInTransaction = 1)
	rollback transaction odbc_keep_temptable_tx    

return(0)
go
go
exec sp_procxmode 'sp_odbc_databases', 'anymode'
go
grant execute on sp_odbc_databases to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go
if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_columns')
begin
	drop procedure sp_odbc_columns
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G% " */
/*      10.0        07/20/93        sproc/columns */
 

/* This is the version for servers which support UNION */

/* This routine is intended for support of ODBC connectivity.  Under no
** circumstances should changes be made to this routine unless they are
** to fix ODBC related problems.  All other users are at there own risk!
**
** Please be aware that any changes made to this file (or any other ODBC
** support routine) will require Sybase to recertify the SQL server as
** ODBC compliant.  This process is currently being managed internally
** by the "Interoperability Engineering Technology Solutions Group" here
** within Sybase.
*/

CREATE PROCEDURE sp_odbc_columns (
				 @table_name		varchar(96),
				 @table_owner		varchar(32) = null,
				 @table_qualifier	varchar(32) = null,
				 @column_name		varchar(96) = null )
AS
    declare @full_table_name    varchar(193)
    declare @table_id int
    declare @char_bin_types   varchar(32)
    
    declare @o_uid              int
    declare @o_name             varchar (32)
    declare @d_data_type        smallint
    declare @d_aux              int
    declare @d_ss_dtype         tinyint
    declare @d_type_name        varchar (32)
    declare @d_data_precision   int
    declare @d_numeric_scale    smallint
    declare @d_numeric_radix    smallint
    declare @d_sql_data_type    smallint
    declare @c_name             varchar (32)
    declare @c_length           int
    declare @c_prec             tinyint
    declare @c_scale            tinyint
    declare @c_type             tinyint
    declare @c_colid            smallint
    declare @c_status           tinyint
    declare @c_cdefault         int
    declare @xtname             varchar (32)
    declare @column_default   	varchar (255)
    declare @ident		bit
--    declare @max_cdefault_len	int
--    declare @cdefault_len	int

    declare @startedInTransaction bit
    if (@@trancount > 0)
  	select @startedInTransaction = 1
    else
        select @startedInTransaction = 0
                                                       

  
    set transaction isolation level 1

    if (@startedInTransaction = 1)
	save transaction odbc_keep_temptable_tx    
 
/* character and binary datatypes */
	select @char_bin_types =
		char(47)+char(39)+char(45)+char(37)+char(35)+char(34)

    if @column_name is null /*	If column name not supplied, match all */
	select @column_name = '%'

    /* Check if the current database is the same as the one provided */
    if @table_qualifier is not null
    begin
		if db_name() != @table_qualifier
		begin	/* 
			** If qualifier doesn't match current database 
			** 18039, Table qualifier must be name of current database
			*/
			raiserror 18039
			return (1)
		end
    end

    if @table_name is null
    begin	/*	If table name not supplied, match all */
		select @table_name = '%'
    end

    if @table_owner is null
    begin	/* If unqualified table name */
		SELECT @full_table_name = @table_name
    end
    else
    begin	/* Qualified table name */
		SELECT @full_table_name = @table_owner + '.' + @table_name
    end

    /* Get Object ID */
    SELECT @table_id = object_id(@full_table_name)


    /* create the temp table to hold column results */
    create table #odbc_columns (
        TABLE_CAT         varchar (32) null,
        TABLE_SCHEM       varchar (32) null,
        TABLE_NAME        varchar (32) null,
        COLUMN_NAME       varchar (32) null,
        DATA_TYPE         smallint null,
        TYPE_NAME         varchar (32) null,
        COLUMN_SIZE       int null,
        BUFFER_LENGTH     int null,
        DECIMAL_DIGITS    smallint null,
        NUM_PREC_RADIX    smallint null,
        NULLABLE          smallint null,
        REMARKS           varchar (32) null,
        COLUMN_DEF        varchar (255) null,
        SQL_DATA_TYPE     smallint null,
        SQL_DATETIME_SUB  smallint null,
        CHAR_OCTET_LENGTH int null,
        ORDINAL_POSITION  int null,
        IS_NULLABLE       varchar (10) null)

--	select @max_cdefault_len = 255

    /* If the table name parameter is valid, get the information */ 
    if ((charindex('%',@full_table_name) = 0) and
		(charindex('_',@full_table_name) = 0)  and
		@table_id != 0)
    begin
      declare odbc_columns_cursor1 cursor for
        SELECT 
               c.cdefault,
               c.colid,
               c.length,
               c.name,
               c.prec,
               c.scale,
               c.status,
               c.type,
               d.aux, 
               d.data_precision,
               d.data_type,
               d.numeric_radix,
               d.numeric_scale,
               d.sql_data_type,
               d.ss_dtype,
		    case 
		     when c.usertype = 80 then t.name
		     when c.usertype = 24 then t.name
		     when c.usertype = 25 then t.name
		    else
			  d.type_name
		    end,               
              
               o.name,
               o.uid,
               xtname,
               convert(bit, (c.status & 0x80))
	FROM
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		sysxtypes x,
		systypes t
	WHERE
		o.id = @table_id
		AND c.id = o.id
		/*
		** We use syscolumn.usertype instead of syscolumn.type
		** to do join with systypes.usertype. This is because
		** for a column which allows null, type stores its
		** Server internal datatype whereas usertype still
		** stores its user defintion datatype.  For an example,
		** a column of type 'decimal NULL', its usertype = 26,
		** representing decimal whereas its type = 106 
		** representing decimaln. nullable in the select list
		** already tells user whether the column allows null.
		** In the case of user defining datatype, this makes
		** more sense for the user.
		*/
		AND c.usertype = t.usertype
		AND t.type = d.ss_dtype
		AND c.xtype *= x.xtid
		AND o.type != 'P'
		AND c.name like @column_name
	AND d.ss_dtype IN (111, 109, 38, 110)	/* Just *N types */
--	AND d.ss_dtype IN (111, 109, 38, 110, 68)	/* Just *N types */	
		AND c.usertype < 100		/* No user defined types */
		
      open odbc_columns_cursor1

      fetch odbc_columns_cursor1 into
        @c_cdefault,
        @c_colid,
        @c_length,
        @c_name,
        @c_prec,
        @c_scale,
        @c_status,
        @c_type,
        @d_aux, 
        @d_data_precision,
        @d_data_type,
        @d_numeric_radix,
        @d_numeric_scale,
        @d_sql_data_type,
        @d_ss_dtype,
        @d_type_name,
        @o_name,
        @o_uid,
        @xtname,
        @ident
        
	while (@@sqlstatus = 0)
        begin
--	if (@c_cdefault is NOT NULL)
--	  begin
--           	exec sp_drv_column_default @c_cdefault, @column_default out
--           	select @cdefault_len= datalength(@column_default)

--		if (@cdefault_len > @max_cdefault_len)
--			select @column_default = "TRUNCATED"

           	/* INTn, FLOATn, DATETIMEn and MONEYn types */
		INSERT INTO #odbc_columns values(
		DB_NAME(),
		USER_NAME(@o_uid),
		@o_name,
		@c_name,
		@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60)),
		/* TYPE_NAME */
		case
	            	when @ident = 1 then 
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))+' identity'
	            	else
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))
		end,
		isnull(convert(int, @c_prec),
			 isnull(convert(int, @d_data_precision),
			convert(int,@c_length)))
			+isnull(@d_aux, convert(int,
			ascii(substring("???AAAFFFCKFOLS",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		isnull(convert(int, @c_length), 
			convert(int, @c_length)) +
			   convert(int, isnull(@d_aux,
			ascii(substring("AAA<BB<DDDHJSPP",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-64)),
		isnull(convert(smallint, @c_scale), 
		       convert(smallint, @d_numeric_scale))
			+convert(smallint,
			isnull(@d_aux,
			ascii(substring("<<<<<<<<<<<<<<?",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60)),
		@d_numeric_radix,
		/* set nullability from status flag */
		convert(smallint, convert(bit, @c_status&8)),
		convert(varchar(254),null),	/* Remarks are NULL */
                @column_default,
                isnull(@d_sql_data_type,
			@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60))),
		convert(smallint,NULL),
            	/*
            	** if the datatype is of type CHAR or BINARY
            	** then set char_octet_length to the same value
            	** assigned in the "prec" column.
            	**
            	** The first part of the logic is:
            	**
            	**   if(@c_type is in (47, 39, 45, 37, 35, 34))
            	**       set char_octet_length = prec;
            	**   else
            	**       set char_octet_length = 0;
            	*/
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision 
		** if not, return a 0 and multiply it by the precision
		*/
		convert(smallint, 
                    	substring('0111111', 
                       	charindex(char(@c_type), 
			@char_bin_types)+1, 1)) * 
                	/* calculate the precision */
                	isnull(convert(int, @c_prec),
                    	isnull(convert(int, @d_data_precision),
                       	convert(int,@c_length)))
                    	+isnull(@d_aux, convert(int,
                       	ascii(substring('???AAAFFFCKFOLS',
                       	2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		convert(int,@c_colid),
		rtrim(substring('NO YES',
                	(convert(smallint, convert(bit, @c_status&8))*3)+1, 3)))
                	
	fetch odbc_columns_cursor1 into
	@c_cdefault,
	@c_colid,
	@c_length,
	@c_name,
	@c_prec,
	@c_scale,
	@c_status,
	@c_type,
	@d_aux, 
	@d_data_precision,
	@d_data_type,
	@d_numeric_radix,
	@d_numeric_scale,
	@d_sql_data_type,
	@d_ss_dtype,
	@d_type_name,
	@o_name,
	@o_uid,
	@xtname,
	@ident
	
--	end		/* end of if	*/
	end	/* end of while */

	deallocate cursor odbc_columns_cursor1
	declare odbc_columns_cursor2 cursor for
	SELECT 
	       c.cdefault,
	       c.colid,
	       c.length,
	       c.name,
	       c.prec,
	       c.scale,
	       c.status,
	       c.type,
	       d.aux, 
	       d.data_precision,
	       d.data_type,
	       d.numeric_radix,
	       d.numeric_scale,
	       d.sql_data_type,
	       d.ss_dtype,
		    case 
		     when c.usertype = 80 then t.name
		     when c.usertype = 24 then t.name
		     when c.usertype = 25 then t.name
		    else
			  d.type_name
		    end,               
	       o.name,
	       o.uid,
	       xtname,
	       convert(bit, (c.status & 0x80))
	FROM
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		sysxtypes x,
		systypes t
	WHERE
		o.id = @table_id
		AND c.id = o.id
		/*
		** We use syscolumn.usertype instead of syscolumn.type
		** to do join with systypes.usertype. This is because
		** for a column which allows null, type stores its
		** Server internal datatype whereas usertype still
		** stores its user defintion datatype.  For an example,
		** a column of type 'decimal NULL', its usertype = 26,
		** representing decimal whereas its type = 106 
		** representing decimaln. nullable in the select list
		** already tells user whether the column allows null.
		** In the case of user defining datatype, this makes
		** more sense for the user.
		*/
		AND c.usertype = t.usertype
		/*
		** We need a equality join with 
		** sybsystemprocs.dbo.spt_datatype_info here so that
		** there is only one qualified row returned from 
		** sybsystemprocs.dbo.spt_datatype_info, thus avoiding
		** duplicates.
		*/
		AND t.type = d.ss_dtype
		AND c.xtype *= x.xtid
		AND o.type != 'P'
		AND c.name like @column_name
	AND (d.ss_dtype NOT IN (111, 109, 38, 110) /* No *N types */
--	AND (d.ss_dtype NOT IN (111, 109, 38, 110, 68) /* No *N types */
			OR c.usertype >= 100) /* User defined types */

      open odbc_columns_cursor2
      fetch odbc_columns_cursor2 into
          @c_cdefault,
          @c_colid,
          @c_length,
          @c_name,
          @c_prec,
          @c_scale,
          @c_status,
          @c_type,
          @d_aux, 
          @d_data_precision,
          @d_data_type,
          @d_numeric_radix,
          @d_numeric_scale,
          @d_sql_data_type,
          @d_ss_dtype,
          @d_type_name,
          @o_name,
          @o_uid,
          @xtname,
          @ident

      while (@@sqlstatus = 0)
      begin
-- 	  if (@c_cdefault is NOT NULL)
-- 	  begin
--	        exec sp_drv_column_default @c_cdefault, @column_default out
--           	select @cdefault_len= datalength(@column_default)

--		if (@cdefault_len > @max_cdefault_len)
--			select @column_default = "TRUNCATED"
		
	   /* All other types including user data types */
		INSERT INTO #odbc_columns values(
		DB_NAME(),
		USER_NAME(@o_uid),
		@o_name,
		@c_name,
		@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60)),
		/* TYPE_NAME */
		case
	            	when @ident = 1 then 
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))+' identity'
	            	else
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))
		end,
		isnull(convert(int, @c_prec),
			 isnull(convert(int, @d_data_precision), 
			convert(int,@c_length)))
			+isnull(@d_aux, convert(int,
			ascii(substring("???AAAFFFCKFOLS",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		isnull(convert(int, @c_length), 
			convert(int, @c_length)) +
			   convert(int, isnull(@d_aux,
			ascii(substring("AAA<BB<DDDHJSPP",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-64)),
		isnull(convert(smallint, @c_scale), 
		       convert(smallint, @d_numeric_scale)) +
			convert(smallint, isnull(@d_aux,
			ascii(substring("<<<<<<<<<<<<<<?",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60)),
		@d_numeric_radix,
		/* set nullability from status flag */
		convert(smallint, convert(bit, @c_status&8)),
		convert(varchar(254),null),	/* Remarks are NULL */
                @column_default,
                isnull(@d_sql_data_type,
			@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60))),
		convert(smallint,NULL),
            	/*
            	** if the datatype is of type CHAR or BINARY
            	** then set char_octet_length to the same value
            	** assigned in the "prec" column.
            	**
            	** The first part of the logic is:
            	**
            	**   if(@c_type is in (47, 39, 45, 37, 35, 34))
            	**       set char_octet_length = prec;
            	**   else
            	**       set char_octet_length = 0;
            	*/
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision 
		** if not, return a 0 and multiply it by the precision
		*/
		convert(smallint, 
			substring('0111111', 
			charindex(char(@c_type), 
			@char_bin_types)+1, 1)) * 
			/* calculate the precision */
			isnull(convert(int, @c_prec),
			isnull(convert(int, @d_data_precision),
			convert(int,@c_length)))
			+isnull(@d_aux, convert(int,
			ascii(substring('???AAAFFFCKFOLS',
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		convert(int,@c_colid),
		rtrim(substring('NO YES',
                	(convert(smallint, convert(bit, @c_status&8))*3)+1, 3)))

	fetch odbc_columns_cursor2 into
	@c_cdefault,
	@c_colid,
	@c_length,
	@c_name,
	@c_prec,
	@c_scale,
	@c_status,
	@c_type,
	@d_aux, 
	@d_data_precision,
	@d_data_type,
	@d_numeric_radix,
	@d_numeric_scale,
	@d_sql_data_type,
	@d_ss_dtype,
	@d_type_name,
	@o_name,
	@o_uid,
	@xtname,
	@ident
              
--	end  /* end of if */              

	end /* while loop */
	deallocate cursor odbc_columns_cursor2
    end
    else
    begin
	/* 
	** This block is for the case where there IS pattern
	** matching done on the table name. 
	*/
	if @table_owner is null /* If owner not supplied, match all */
			select @table_owner = '%'

	declare odbc_columns_cursor3 cursor for
	select
		c.cdefault,
		c.colid,
		c.length,
		c.name,
		c.prec,
		c.scale,
		c.status,
		c.type,
		d.aux, 
		d.data_precision,
		d.data_type,
		d.numeric_radix,
		d.numeric_scale,
		d.sql_data_type,
		d.ss_dtype,
		    case 
		     when c.usertype = 80 then t.name
		     when c.usertype = 24 then t.name
		     when c.usertype = 25 then t.name
		    else
			  d.type_name
		    end,               
		o.name,
		o.uid,
		xtname,
		convert(bit, (c.status & 0x80))
	FROM
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		sysxtypes x,
		systypes t
	WHERE
		o.name like @table_name
		AND user_name(o.uid) like @table_owner
		AND o.id = c.id
		/*
		** We use syscolumn.usertype instead of syscolumn.type
		** to do join with systypes.usertype. This is because
		** for a column which allows null, type stores its
		** Server internal datatype whereas usertype still
		** stores its user defintion datatype.  For an example,
		** a column of type 'decimal NULL', its usertype = 26,
		** representing decimal whereas its type = 106 
		** representing decimaln. nullable in the select list
		** already tells user whether the column allows null.
		** In the case of user defining datatype, this makes
		** more sense for the user.
		*/
		AND c.usertype = t.usertype
		AND t.type = d.ss_dtype
		AND o.type != 'P'
		AND c.xtype *= x.xtid
		AND c.name like @column_name
	AND d.ss_dtype IN (111, 109, 38, 110)	/* Just *N types */
--	AND d.ss_dtype IN (111, 109, 38, 110, 68)	/* Just *N types */	
		AND c.usertype < 100

        open odbc_columns_cursor3

	fetch odbc_columns_cursor3 into
		@c_cdefault,
		@c_colid,
		@c_length,
		@c_name,
		@c_prec,
		@c_scale,
		@c_status,
		@c_type,
		@d_aux, 
		@d_data_precision,
		@d_data_type,
		@d_numeric_radix,
		@d_numeric_scale,
		@d_sql_data_type,
		@d_ss_dtype,
		@d_type_name,
		@o_name,
		@o_uid,
		@xtname,
		@ident


        /* INTn, FLOATn, DATETIMEn and MONEYn types */

        while (@@sqlstatus = 0)
        begin
--	  if (@c_cdefault is NOT NULL)
--	  begin
--          	exec sp_drv_column_default @c_cdefault, @column_default out
--           	select @cdefault_len= datalength(@column_default)

--		  if (@cdefault_len > @max_cdefault_len)
--		  	select @column_default = "TRUNCATED"
          
          /* INTn, FLOATn, DATETIMEn and MONEYn types */
		INSERT INTO #odbc_columns values(
		DB_NAME(),
		USER_NAME(@o_uid),
		@o_name,
		@c_name,
		@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60)),
		/* TYPE_NAME */
		case
	            	when @ident = 1 then 
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))+' identity'
	            	else
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))
		end,
		isnull(convert(int, @c_prec),
			isnull(convert(int, @d_data_precision),
				 convert(int, @c_length)))
			+isnull(@d_aux, convert(int,
			ascii(substring("???AAAFFFCKFOLS",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		isnull(convert(int, @c_length), 
			convert(int,@c_length)) +
			   convert(int, isnull(@d_aux,
			ascii(substring("AAA<BB<DDDHJSPP",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-64)),
		isnull(convert(smallint, @c_scale), 
		       convert(smallint, @d_numeric_scale)) +
			convert(smallint, isnull(@d_aux,
			ascii(substring("<<<<<<<<<<<<<<?",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60)),
		@d_numeric_radix,
		/* set nullability from status flag */
		convert(smallint, convert(bit, @c_status&8)),
		convert(varchar(254),null),	/* Remarks are NULL */
                @column_default,
                isnull(@d_sql_data_type,
			@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60))),
		convert(smallint,NULL),
            	/*
            	** if the datatype is of type CHAR or BINARY
            	** then set char_octet_length to the same value
            	** assigned in the "prec" column.
            	**
            	** The first part of the logic is:
            	**
            	**   if(@c_type is in (47, 39, 45, 37, 35, 34))
            	**       set char_octet_length = prec;
            	**   else
            	**       set char_octet_length = 0;
            	*/
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision 
		** if not, return a 0 and multiply it by the precision
		*/
		convert(smallint, 
                    	substring('0111111', 
                       	charindex(char(@c_type), 
			@char_bin_types)+1, 1)) * 
                	/* calculate the precision */
                	isnull(convert(int, @c_prec),
                    	isnull(convert(int, @d_data_precision),
                       	convert(int,@c_length)))
                    	+isnull(@d_aux, convert(int,
                       	ascii(substring('???AAAFFFCKFOLS',
                       	2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		convert(int,@c_colid),
                rtrim(substring('NO YES',
                	(convert(smallint, convert(bit, @c_status&8))*3)+1, 3)))
	fetch odbc_columns_cursor3 into
		@c_cdefault,
		@c_colid,
		@c_length,
		@c_name,
		@c_prec,
		@c_scale,
		@c_status,
		@c_type,
		@d_aux, 
		@d_data_precision,
		@d_data_type,
		@d_numeric_radix,
		@d_numeric_scale,
		@d_sql_data_type,
		@d_ss_dtype,
		@d_type_name,
		@o_name,
		@o_uid,
		@xtname,
		@ident
--           end 	/* end of if	*/

        end /* while loop */

	deallocate cursor odbc_columns_cursor3
        declare odbc_columns_cursor4 cursor for
        SELECT 
               c.cdefault,
               c.colid,
               c.length,
               c.name,
               c.prec,
               c.scale,
               c.status,
               c.type,
               d.aux, 
               d.data_precision,
               d.data_type,
               d.numeric_radix,
               d.numeric_scale,
               d.sql_data_type,
               d.ss_dtype,
		    case 
		     when c.usertype = 80 then t.name
		     when c.usertype = 24 then t.name
		     when c.usertype = 25 then t.name
		    else
			  d.type_name
		    end,               
               o.name,
               o.uid,
               xtname,
               convert(bit, (c.status & 0x80))
	FROM
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		sysxtypes x,
		systypes t
	WHERE
		o.name like @table_name
		AND user_name(o.uid) like @table_owner
		AND o.id = c.id
		/*
		** We use syscolumn.usertype instead of syscolumn.type
		** to do join with systypes.usertype. This is because
		** for a column which allows null, type stores its
		** Server internal datatype whereas usertype still
		** stores its user defintion datatype.  For an example,
		** a column of type 'decimal NULL', its usertype = 26,
		** representing decimal whereas its type = 106 
		** representing decimaln. nullable in the select list
		** already tells user whether the column allows null.
		** In the case of user defining datatype, this makes
		** more sense for the user.
		*/
		AND c.usertype = t.usertype
		/*
		** We need a equality join with 
		** sybsystemprocs.dbo.spt_datatype_info here so that
		** there is only one qualified row returned from 
		** sybsystemprocs.dbo.spt_datatype_info, thus avoiding
		** duplicates.
		*/
		AND t.type = d.ss_dtype
		AND c.name like @column_name
		AND o.type != 'P'
		AND c.xtype *= x.xtid
		AND c.name like @column_name
	AND (d.ss_dtype NOT IN (111, 109, 38, 110) /* No *N types */
--	AND (d.ss_dtype NOT IN (111, 109, 38, 110, 68) /* No *N types */
			OR c.usertype >= 100) /* User defined types */

	open odbc_columns_cursor4

	fetch odbc_columns_cursor4 into
		@c_cdefault,
		@c_colid,
		@c_length,
		@c_name,
		@c_prec,
		@c_scale,
		@c_status,
		@c_type,
		@d_aux, 
		@d_data_precision,
		@d_data_type,
		@d_numeric_radix,
		@d_numeric_scale,
		@d_sql_data_type,
		@d_ss_dtype,
		@d_type_name,
		@o_name,
		@o_uid,
		@xtname,
		@ident


        while (@@sqlstatus = 0)
        begin
--	  if (@c_cdefault is NOT NULL)
--	  begin
--	        exec sp_drv_column_default @c_cdefault, @column_default out
--           	select @cdefault_len= datalength(@column_default)

--		if (@cdefault_len > @max_cdefault_len)
--			select @column_default = "TRUNCATED"
          
          /* All other types including user data types */
		INSERT INTO #odbc_columns values(
		/* TABLE_CAT */
		DB_NAME(),
            	/* TABLE_SCHEM */
		USER_NAME(@o_uid),
		/* TABLE_NAME */
		@o_name,
		/*COLUMN_NAME*/
		@c_name,
		/* DATA_TYPE */
		@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60)),
		/* TYPE_NAME */
		case
	            	when @ident = 1 then 
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))+' identity'
	            	else
			rtrim(substring(@d_type_name,
			1+isnull(@d_aux,
			ascii(substring("III<<<MMMI<<A<A",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60), 18))
		end,
		/* COLUMN_SIZE */  	
		isnull(convert(int, @c_prec),
			isnull(convert(int, @d_data_precision),
			convert(int,@c_length)))
			+isnull(@d_aux, convert(int,
			ascii(substring("???AAAFFFCKFOLS",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		/* BUFFER_LENGTH */ 			
		isnull(convert(int, @c_length), 
			convert(int, @c_length)) +
			convert(int, isnull(@d_aux,
			ascii(substring("AAA<BB<DDDHJSPP",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-64)),
		/* DECIMAL_DIGITS */ 	
		isnull(convert(smallint, @c_scale),
			convert(smallint, @d_numeric_scale)) +
			convert(smallint, isnull(@d_aux,
			ascii(substring("<<<<<<<<<<<<<<?",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,
			1))-60)),
		/* NUM_PREC_RADIX */	
		@d_numeric_radix,
		/* NULLABLE */
		/* set nullability from status flag */
		convert(smallint, convert(bit, @c_status&8)),
		/* REMARKS */
		convert(varchar(254),null),
		/* COLUMN_DEF */
                @column_default,
                /* SQL_DATA_TYPE */
                isnull(@d_sql_data_type,
			@d_data_type+convert(smallint,
			isnull(@d_aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))
			-60))),
		/* SQL_DATETIME_SUB */	
		convert(smallint,NULL),
            	/*
            	** if the datatype is of type CHAR or BINARY
            	** then set char_octet_length to the same value
            	** assigned in the "prec" column.
            	**
            	** The first part of the logic is:
            	**
            	**   if(@c_type is in (47, 39, 45, 37, 35, 34))
            	**       set char_octet_length = prec;
            	**   else
            	**       set char_octet_length = 0;
            	*/
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision 
		** if not, return a 0 and multiply it by the precision
		*/
		/* CHAR_OCTET_LENGTH */
		convert(smallint, 
			substring('0111111', 
			charindex(char(@c_type), 
			@char_bin_types)+1, 1)) * 
			/* calculate the precision */
			isnull(convert(int, @c_prec),
			isnull(convert(int, @d_data_precision),
			convert(int,@c_length)))
			+isnull(@d_aux, convert(int,
			ascii(substring('???AAAFFFCKFOLS',
			2*(@d_ss_dtype%35+1)+2-8/@c_length,1))-60)),
		/* ORDINAL_POSITION */	
		convert(int,@c_colid),
		/* IS_NULLABLE */
		rtrim(substring('NO YES',
                	(convert(smallint, convert(bit, @c_status&8))*3)+1, 3)))
	fetch odbc_columns_cursor4 into
		@c_cdefault,
		@c_colid,
		@c_length,
		@c_name,
		@c_prec,
		@c_scale,
		@c_status,
		@c_type,
		@d_aux, 
		@d_data_precision,
		@d_data_type,
		@d_numeric_radix,
		@d_numeric_scale,
		@d_sql_data_type,
		@d_ss_dtype,
		@d_type_name,
		@o_name,
		@o_uid,
		@xtname,
		@ident
--           end	/* end of if 	*/

         end /* while loop */ 
         
         deallocate cursor odbc_columns_cursor4
end
SELECT * FROM #odbc_columns ORDER BY TABLE_SCHEM, TABLE_NAME, ORDINAL_POSITION
drop table #odbc_columns
if (@startedInTransaction = 1)
   rollback transaction odbc_keep_temptable_tx    

return(0)
go
exec sp_procxmode 'sp_odbc_columns', 'anymode'
go
grant execute on sp_odbc_columns to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_datatype_info')
begin
	drop procedure sp_odbc_datatype_info
end
go





/* 
** Sccsid = "%Z% generic/sproc/%M% %I% %G%"
**
** History:
**	mm/yy		Author					Comments
**	12/06		Meena Ramakrishnan		Changes to conform to the ODBC API 
**										of returning the system types in any
**										given sql data type first before the user defined types
**	
**	This stored procedure has been ported from the ASE stored procedure sp_datatype_info
**
**	10.0	steven	1.1	07/13/93	sproc/src/datatype_info
**						Ported from MS catalog SP's
**
** Implementation Notes:
** 	The messiness of 'sp_odbc_data_type_info' was to get around the
** problem of returning the correct lengths for user defined types.  The
** join on the type name ensures all user defined types are returned, but
** this puts a null in the data_type column.  By forcing an embedded
** select and correlating it with the current row in systypes, we get the
** correct data_type mapping even for user defined types.  
**
**	parameters: data_type  of type int
*/

create procedure sp_odbc_datatype_info
@data_type int = 0,			/* Provide datatype_info for type # */
@odbc_ver  int = 3			/* Provide result set for ODBC 3.0 API # */
as

declare @startedInTransaction bit

if (@@trancount > 0)
   select @startedInTransaction = 1
else
   select @startedInTransaction = 0
                                                       

if (@startedInTransaction = 1)
   save transaction odbc_keep_temptable_tx    
   
set @data_type =
    case @data_type
        when null then 0
        when 91 then 9
        when 92 then 10
        when 93 then 11
        else @data_type
    end

 
select
    TYPE_NAME =
        cast(
            case t.name
                when 'usmallint' then 'unsigned smallint'
                when 'uint' then 'unsigned int'
                when 'ubigint' then 'unsigned bigint'
                else t.name
            end
            as varchar(30)),
    DATA_TYPE =
        cast(
            case
                when d.data_type = 9 and @odbc_ver = 3 then 91
                when d.data_type = 10 and @odbc_ver = 3 then 92
                when d.data_type = 11 and @odbc_ver = 3 then 93
                when t.name ='unichar' and @odbc_ver in (2,3) then -8
                when t.name ='univarchar'and @odbc_ver in (2,3) then -9
                else d.data_type
            end
            as smallint),
    COLUMN_SIZE = cast(isnull(d.data_precision, t.length / case when t.name in ('univarchar', 'unichar') then 2 else 1 end) as int),
    LITERAL_PREFIX = cast(d.literal_prefix as varchar(30)),
    LITERAL_SUFFIX = cast(d.literal_suffix as varchar(30)),
    CREATE_PARAMS = cast(case when e.create_params = 'max length' or d.data_type in (1,12) then 'length' else e.create_params end as varchar (30)),
    NULLABLE = cast(d.nullable as smallint),
    CASE_SENSITIVE = cast(d.case_sensitive as smallint),
    SEARCHABLE = cast(d.searchable as smallint),
    UNSIGNED_ATTRIBUTE = cast(d.unsigned_attribute as smallint),
    FIXED_PREC_SCALE = cast(d.money as smallint),
    AUTO_UNIQUE_VALUE = cast(d.auto_increment as smallint),
    LOCAL_TYPE_NAME = cast(case when t.name = 'timestamp' then 'timestamp' else d.local_type_name end as varchar(30)),
    MINIMUM_SCALE = cast(case when d.data_type in (10,11) then 0 else d.minimum_scale end as smallint),
    MAXIMUM_SCALE = cast(case when d.data_type in (10,11) then 3 else d.minimum_scale end as smallint),
    SQL_DATA_TYPE =
        cast(
            case
                when d.data_type in (9,10,11) then 9
                when t.name = 'unichar' then -8
                when t.name = 'univarchar' then -9
                else isnull(d.sql_data_type, d.data_type + d.aux)
            end
            as smallint),
    SQL_DATETIME_SUB =
        cast(case d.data_type
                when 9 then 1
                when 10 then 2
                when 11 then 3
                else d.sql_datetime_sub
            end
            as smallint),
    NUM_PREC_RADIX = cast(case when d.data_type in (2,3,4,5,6,7,-7,-6) then 10 else d.num_prec_radix end as int),
    INTERVAL_PRECISION = cast(d.interval_precision as smallint)
from sybsystemprocs.dbo.spt_datatype_info d
join systypes t
    on t.type = d.ss_dtype
left join sybsystemprocs.dbo.spt_datatype_info_ext e
    on e.user_type = t.usertype
where d.data_type = case @data_type when 0 then d.data_type else @data_type end
and t.name not in ('longsysname','datetimn','floatn','intn','moneyn','uintn')   -- not real datatypes
order by
    DATA_TYPE,
    t.usertype,
    TYPE_NAME

if (@startedInTransaction = 1)
   rollback transaction odbc_keep_temptable_tx    

return (0)
go
exec sp_procxmode 'sp_odbc_datatype_info', 'anymode'
go
grant execute on sp_odbc_datatype_info to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_getversioncolumns')
begin
	drop procedure sp_odbc_getversioncolumns
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */
/*	10.0	1.0	9 JUL 93	sproc/src/special_columns */

/* 
** Messages for "sp_odbc_getversioncolumns"
**
** 17863, "There is no table named %1! in the current database."
** 18039, "Table qualifier must be name of current database."
** 18042, "Illegal value for 'col_type' argument. Legal values are 'V' or 'R'."
**
*/

create procedure sp_odbc_getversioncolumns (
				 @table_name		varchar(96),
				 @table_owner		varchar(32) = null,
				 @table_qualifier	varchar(32) = null,
				 @col_type		char(1) = 'R' )
as
	declare @indid			int
	declare @table_id		int
	declare @dbname			varchar(32)
	declare @full_table_name	varchar(193)
	declare @version		varchar(32)

	if @@trancount = 0
	begin
		set chained off
	end

	set transaction isolation level 1

	/* get database name */
	select @dbname = db_name()

	/* we don't want a temp table unless we're in tempdb */
	if (@table_name like "#%" and @dbname != 'tempdb')
-- 	if (@table_name like "#%" and @dbname != 'tempdb')		-- 12.0
-- 	if @table_name like "#%" and @dbname != db_name(tempdb_id())	-- 12.5

	begin	
		/* 17863, "There is no table named %1! in the current database." */
		raiserror 17863, @table_name
		return (1)
	end

	if @table_qualifier is not null
	begin
		if @dbname != @table_qualifier
		begin	
			/* 18039, "Table qualifier must be name of current database." */
			raiserror 18039
			return (1)
		end
	end

	if @table_owner is null
	begin	/* if unqualified table name */
		select @full_table_name = @table_name
	end
	else
	begin	/* qualified table name */
		select @full_table_name = @table_owner + '.' + @table_name
	end

	/* get object ID */
	select @table_id = object_id(@full_table_name)

	if @col_type = 'V'
	begin /* if ROWVER, just run that query */
		select
			SCOPE = convert(smallint, 0),
			COLUMN_NAME = c.name,
			DATA_TYPE = d.data_type + convert(smallint,
					isnull(d.aux,
					ascii(substring("666AAA@@@CB??GG",
					2*(d.ss_dtype%35+1)+2-8/c.length,1))
					-60)),
			TYPE_NAME = t.name,
			COLUMN_SIZE = isnull(d.data_precision,
					convert(int,c.length))
					+ isnull(d.aux, convert(int,
					ascii(substring("???AAAFFFCKFOLS",
					2*(d.ss_dtype%35+1)+2-8/c.length,1))
					-60)),
			BUFFER_LENGTH = isnull(d.length, convert(int,c.length))
					+ convert(int,
					isnull(d.aux,
					ascii(substring("AAA<BB<DDDHJSPP",
					2*(d.ss_dtype%35+1)+2-8/c.length, 1))
					-64)),
			DECIMAL_DIGITS = d.numeric_scale + convert(smallint,
					isnull(d.aux,
					ascii(substring("<<<<<<<<<<<<<<?",
					2*(d.ss_dtype%35+1)+2-8/c.length, 1))
					-60)),
			PSEUDO_COLUMN=convert(smallint,1)						
		from
			systypes t, syscolumns c, sybsystemprocs.dbo.spt_datatype_info d
		where
			c.id = @table_id
			and c.type = d.ss_dtype
			and c.usertype = 80	/* TIMESTAMP */
			and t.usertype = 80	/* TIMESTAMP */
			
		return (0)
	end

	if @col_type != 'R'
	begin
		/* 18042, "Illegal value for 'col_type' argument. Legal values are 'V' or 'R'." */

		raiserror 18042
		return (1)
	end

	/* An identity column is the most optimal unique identifier */
	if exists (select colid from syscolumns
		where id = @table_id and (status&128) = 128)
	begin
	    select
		SCOPE = convert(smallint, 0),
		COLUMN_NAME = c.name,
		DATA_TYPE = d.data_type + convert(smallint,
					isnull(d.aux,
					ascii(substring("666AAA@@@CB??GG",
					2*(d.ss_dtype%35+1)+2-8/c.length,1))
					-60)),
		TYPE_NAME = rtrim(substring(d.type_name,
					1 + isnull(d.aux,
					ascii(substring("III<<<MMMI<<A<A",
					2*(d.ss_dtype%35+1)+2-8/c.length, 1))
					-60), 18)),
		COLUMN_SIZE = isnull(d.data_precision, convert(int,c.length))
					+ isnull(d.aux, convert(int,
					ascii(substring("???AAAFFFCKFOLS",
					2*(d.ss_dtype%35+1)+2-8/c.length,1))
					-60)),
		BUFFER_LENGTH = isnull(d.length, convert(int,c.length))
					+ convert(int, isnull(d.aux,
					ascii(substring("AAA<BB<DDDHJSPP",
					2*(d.ss_dtype%35+1)+2-8/c.length, 1))
					-64)),
		DECIMAL_DIGITS = d.numeric_scale + convert(smallint,
					isnull(d.aux,
					ascii(substring("<<<<<<<<<<<<<<?",
					2*(d.ss_dtype%35+1)+2-8/c.length, 1))
					-60)),
		PSEUDO_COLUMN=convert(smallint,1)					
	    from
		syscolumns c,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t
	    where
		c.id = @table_id
		and (c.status&128) = 128
		and c.type = d.ss_dtype
		and c.usertype *= t.usertype

	    return (0)
	end

	/* ROWID, now find the id of the 'best' index for this table */

	select @indid = (
		select min(indid)
		from sysindexes
		where
			status & 2 = 2		/* if unique index */
			and id = @table_id
			and indid > 0)		/* eliminate table row */

	 select
		SCOPE = convert(smallint, 0),
		COLUMN_NAME = index_col(@full_table_name,indid,c.colid),
		DATA_TYPE = d.data_type + convert(smallint,
					isnull(d.aux,
					ascii(substring("666AAA@@@CB??GG",
					2*(d.ss_dtype%35+1)+2-8/c2.length,1))
					-60)),
		TYPE_NAME = rtrim(substring(d.type_name,
					1 + isnull(d.aux,
					ascii(substring("III<<<MMMI<<A<A",
					2*(d.ss_dtype%35+1)+2-8/c2.length, 1))
					-60), 18)),
		COLUMN_SIZE = isnull(d.data_precision, convert(int,c2.length))
					+ isnull(d.aux, convert(int,
					ascii(substring("???AAAFFFCKFOLS",
					2*(d.ss_dtype%35+1)+2-8/c2.length,1))
					-60)),
		BUFFER_LENGTH = isnull(d.length, convert(int,c2.length))
					+ convert(int, isnull(d.aux,
					ascii(substring("AAA<BB<DDDHJSPP",
					2*(d.ss_dtype%35+1)+2-8/c2.length, 1))
					-64)),
		DECIMAL_DIGITS = d.numeric_scale + convert(smallint,
					isnull(d.aux,
					ascii(substring("<<<<<<<<<<<<<<?",
					2*(d.ss_dtype%35+1)+2-8/c2.length, 1))
					-60)),
		PSEUDO_COLUMN=convert(smallint,1)					
	from
		sysindexes x,
		syscolumns c,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t,
		syscolumns c2	/* self-join to generate list of index
				** columns and to extract datatype names */
	where
		x.id = @table_id
		and c2.name = index_col(@full_table_name, @indid,c.colid)
		and c2.id =x.id
		and c.id = x.id
		and c.colid < keycnt + (x.status & 16) / 16
		and x.indid = @indid
		and c2.type = d.ss_dtype
		and c2.usertype *= t.usertype

	return (0)
go
go
exec sp_procxmode 'sp_odbc_getversioncolumns', 'anymode'
go
grant execute on sp_odbc_getversioncolumns to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_getcolumnprivileges')
begin
	drop procedure sp_odbc_getcolumnprivileges
end
go

/* Sccsid = "%Z% generic/sproc/src/%M% %I% %G%" */

create procedure sp_odbc_getcolumnprivileges ( 
                        @table_name  varchar(96),
                        @table_owner varchar(32) = null,
                        @table_qualifier varchar(32)= null,
                        @column_name varchar(96) = null)

as        

    declare @owner_id    		int
    declare @full_table_name    	varchar(193)
    declare @tab_id 			int	    /* object id of the table specified */
    declare @startedInTransaction bit


    if (@@trancount > 0)
       select @startedInTransaction = 1
    else
       select @startedInTransaction = 0
                                                       


    set nocount on
    /*
    ** set the transaction isolation level
    */
    if @@trancount = 0
    begin
	   set chained off
    end
   
    set transaction isolation level 1

    if (@startedInTransaction = 1)
       save transaction odbc_keep_temptable_tx    

    /*
    **  Check to see that the table is qualified with database name
    */
    if @table_name like "%.%.%" 
    begin
		/* 18021, "Object name can only be qualified with owner name" */
		raiserror 18021
		return (1)
    end

    /*  If this is a temporary table; object does not belong to 
    **  this database; (we should be in our temporary database)
    */
    if (@table_name like "#%" and db_name() != 'tempdb')
    begin
		/* 
		** 17676, "This may be a temporary object. Please execute 
		** procedure from your temporary database."
		*/
		raiserror 17676
		return (1)
    end

    /*
    ** The table_qualifier should be same as the database name. Do the sanity check
    ** if it is specified
    */
    if (@table_qualifier is null) or (@table_qualifier = '')
	/* set the table qualifier name */
	select @table_qualifier = db_name ()
    else
    begin
        if db_name() != @table_qualifier
        begin
			raiserror 18039
	     	return (1)
		end
    end
   
    /* 
    ** if the table owner is not specified, it will be taken as the id of the
    ** user executing this procedure. Otherwise find the explicit table name prefixed
    ** by the owner id
    */
    if (@table_owner is null) or (@table_owner = '')
	        select @full_table_name = @table_name
    else
    begin
	if (@table_name like "%.%") and
	    substring (@table_name, 1, charindex(".", @table_name) -1) != @table_owner
	begin
	 	/* 18011, Object name must be qualified with the owner name * */
		raiserror 18011
		return (1)
	end
	
	if not (@table_name like "%.%")
        	select @full_table_name = @table_owner + '.' + @table_name
	else
	        select @full_table_name = @table_name

    end

    /* 
    ** check to see if the specified table exists or not
    */

    select @tab_id = object_id(@full_table_name)
    if (@tab_id is null)
    begin
		raiserror 17492
		return (1)
    end


    /*
    ** check to see if the @tab_id indeeed represents a table or a view
    */

    if not exists (select * 
                  from   sysobjects
                  where (@tab_id = id) and
	                ((type = 'U') or
                        (type = 'S') or
		        (type = 'V')))
    begin
		raiserror 17492
		return (1)
    end
 

    /*
    ** if the column name is not specified, set the column name to wild 
	** character such it matches all the columns in the table
    */
    if @column_name is null
        select @column_name = '%'

    else
    begin
     /*
	 ** check to see if the specified column is indeed a column belonging
	 ** to the table
	 */
         if not exists (select * 
                        from syscolumns
			where (id = @tab_id) and
			      (name like @column_name))
	 begin
		raiserror 17563, @column_name
		return (1)
	end
    end

   /* Create temp table to store results from sp_aux_computeprivs */
    create table #results_table
	 (TABLE_CAT		varchar (32),
	  TABLE_SCHEM		varchar (32),
	  TABLE_NAME		varchar (32),
	  COLUMN_NAME		varchar (32) NULL,
	  GRANTOR		varchar (32),
	  GRANTEE 		varchar (32),
	  PRIVILEGE		varchar (32),
	  IS_GRANTABLE		varchar (3))


   /*
   ** declare cursor to cycle through all possible columns
   */
   declare cursor_columns cursor
	for select name from syscolumns 
	    where (id = @tab_id) 
	      and (name like @column_name)

   /*
   ** For each column in the list, generate privileges
   */
   open cursor_columns
   fetch cursor_columns into @column_name
   while (@@sqlstatus = 0)
   begin

	/* 
	** compute the table owner id
	*/

	select @owner_id = uid
	from   sysobjects
	where  id = @tab_id


	/*
	** get table owner name
	*/

	select @table_owner = name 
	from sysusers 
	where uid = @owner_id

	exec sp_odbc_computeprivs @table_name, @table_owner, @table_qualifier, 
			     @column_name, 1, @tab_id

	set nocount off 	

	fetch cursor_columns into @column_name
   end

   close cursor_columns
   deallocate cursor cursor_columns

   /* Print out results */ 
   select distinct * from #results_table
   order by COLUMN_NAME, GRANTEE

drop table #results_table
if (@startedInTransaction = 1)
   save transaction odbc_keep_temptable_tx    

return (0)
go
exec sp_procxmode 'sp_odbc_getcolumnprivileges', 'anymode'
go
grant execute on sp_odbc_getcolumnprivileges to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_tables')
begin
	drop procedure sp_odbc_tables
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */
/*	10.0	1.1	06/16/93	sproc/tables */

/*
** Messages for "sp_odbc_tables"         18039
**
** 17676, "This may be a temporary object. Please execute procedure from your 
**         temporary database."
**
** 18039, "Table qualifier must be name of current database"
**
*/
create procedure sp_odbc_tables
@table_name		varchar(96)  = null,
@table_owner     	varchar(32)  = null,
@table_qualifier 	varchar(32)  = null,
@table_type		varchar(100) = null
as

declare @type1 varchar(3)
declare @tableindex int


if @@trancount = 0
begin
	set chained off
end

set transaction isolation level 1

/* temp table */
if (@table_name like "#%" and
   db_name() != 'tempdb')
begin
	/*
        ** Can return data about temp. tables only in session's temporary db
        */
		raiserror 17676
	return(1)
end

/*
** Special feature #1:	enumerate databases when owner and name
** are blank but qualifier is explicitly '%'.  
*/
if @table_qualifier = '%' and
	(@table_owner = '' or @table_owner is null) and
	(@table_name = '' or @table_name is null)
begin	

	/*
	** If enumerating databases 
	*/
	select
		TABLE_CAT = name,
		TABLE_SCHEM = null,
		TABLE_NAME = null,
		TABLE_TYPE= 'Database',

		/*
		** Remarks are NULL 
		*/
		REMARKS = convert(varchar(254),null)

		from master..sysdatabases

		/*
		** eliminate MODEL database 
		*/
		where name != 'model'
		order by TABLE_CAT
end

/*
** Special feature #2:	enumerate owners when qualifier and name
** are blank but owner is explicitly '%'.
*/
else if @table_qualifier = '' and
	@table_owner = '%' and
	(@table_name = '' or @table_name is null)
	begin	

		/*
		** If enumerating owners 
		*/
		select distinct
			TABLE_CAT = null,
			TABLE_SCHEM = user_name(uid),
			TABLE_NAME = null,
			TABLE_TYPE = 'Owner',

		/*
		** Remarks are NULL 
		*/
		REMARKS = convert(varchar(254),null)

		from sysobjects
		order by TABLE_SCHEM
	end
	else
	begin 
		/*
		** end of special features -- do normal processing 
		*/
		if @table_qualifier is not null
		begin
			if db_name() != @table_qualifier
			begin
				if @table_qualifier = ''
				begin  	

					/*
					** If empty qualifier supplied
					** Force an empty result set 
					*/
					select @table_name = ''
					select @table_owner = ''
				end
				else
				begin

					/*
					** If qualifier doesn't match current 
					** database. 
					*/
					raiserror 18039
					return 1
				end
			end
		end
		if @table_type is null
		begin	

			/*
			** Select all ODBC supported table types 
			*/
			select @type1 = 'SUV'
		end
		else
		begin
			/*
			** TableType are case sensitive if CS server 
			*/
			select @type1 = null

			/*
			** Add System Tables 
			*/
			if (charindex("'SYSTEM TABLE'",@table_type) != 0)
				select @type1 = @type1 + 'S'

			/*
			** Add User Tables 
			*/
			if (charindex("'TABLE'",@table_type) != 0)
				select @type1 = @type1 + 'U'

			/*
			** Add Views 
			*/
			if (charindex("'VIEW'",@table_type) != 0)
				select @type1 = @type1 + 'V'
		end
		if @table_name is null
		begin	

			/*
			** If table name not supplied, match all 
			*/
			select @table_name = '%'
		end
		else
		begin
			if (@table_owner is null) and 
			   (charindex('%', @table_name) = 0)
			begin	

			/*
			** If owner not specified and table is specified 
			*/
				if exists (select * from sysobjects
					where uid = user_id()
					and id = object_id(@table_name)
					and (type = 'U' or type = 'V' 
						or type = 'S'))
				begin	

				/*
				** Override supplied owner w/owner of table 
				*/
					select @table_owner = user_name()
				end
			end
		end


		/*
		** If no owner supplied, force wildcard 
		*/
		if @table_owner is null 
			select @table_owner = '%'
		select
			TABLE_CAT = db_name(),
			TABLE_SCHEM = user_name(o.uid),
			TABLE_NAME = o.name,
			TABLE_TYPE = rtrim ( 
					substring('SYSTEM TABLE            TABLE       VIEW       ',
					/*
					** 'S'=0,'U'=2,'V'=3 
					*/
					(ascii(o.type)-83)*12+1,12)),

			/*
			** Remarks are NULL
			*/
			REMARKS = convert(varchar(254),null)

		from sysobjects o
		where
			/* Special case for temp. tables.  Match ids */
			(o.name like @table_name or o.id=object_id(@table_name))
			and user_name(o.uid) like @table_owner

			/*
			** Only desired types
			*/
			and charindex(substring(o.type,1,1),@type1)! = 0 
		and (
                suser_id() = 1          /* User is the System Administrator */
                or o.uid = user_id()    /* User created the object */
                                        /* here's the magic..select the highest
                                        ** precedence of permissions in the
                                        ** order (user,group,public)
                                        */
 
                /*
                ** The value of protecttype is
                **
                **      0  for grant with grant
                **      1  for grant and,
                **      2  for revoke
                **
                ** As protecttype is of type tinyint, protecttype/2 is
                ** integer division and will yield 0 for both types of
                ** grants and will yield 1 for revoke, i.e., when
                ** the value of protecttype is 2.  The XOR (^) operation
                ** will reverse the bits and thus (protecttype/2)^1 will
                ** yield a value of 1 for grants and will yield a
                ** value of zero for revoke.
                **
	        ** For groups, uid = gid. We shall use this to our advantage.
                **
                ** If there are several entries in the sysprotects table
                ** with the same Object ID, then the following expression
                ** will prefer an individual uid entry over a group entry
                **
                ** For example, let us say there are two users u1 and u2
                ** with uids 4 and 5 respectiveley and both u1 and u2
                ** belong to a group g12 whose uid is 16390.  table t1
                ** is owned by user u0 and user u0 performs the following
                ** actions:
                **
                **      grant select on t1 to g12
                **      revoke select on t1 from u1
                **
                ** There will be two entries in sysprotects for the object t1,
                ** one for the group g12 where protecttype = grant (1) and
                ** one for u1 where protecttype = revoke (2).
                **
                ** For the group g12, the following expression will
                ** evaluate to:
                **
                **      ((abs(16390-16390)*2) + ((1/2)^1)
                **      = ((0) + (0)^1) = 0 + 1 = 1
                **
                ** For the user entry u1, it will evaluate to:
                **
                **      (((+)*abs(4-16390)*2) + ((2/2)^1))
                **      = (abs(-16386)*2 + (1)^1)
                **      = 16386*2 + 0 = 32772
                **
                ** As the expression evaluates to a bigger number for the
                ** user entry u1, select max() will chose 32772 which,
                ** ANDed with 1 gives 0, i.e., sp_odbc_tables will not display
                ** this particular table to the user.
                **
                ** When the user u2 invokes sp_odbc_tables, there is only one
                ** entry for u2, which is the entry for the group g12, and
                ** so the group entry will be selected thus allowing the
                ** table t1 to be displayed.
                **
		** ((select max((abs(uid-u.gid)*2)
	        ** 		+ ((protecttype/2)^1))
         	**
                ** Notice that multiplying by 2 makes the number an
                ** even number (meaning the last digit is 0) so what
                ** matters at the end is (protecttype/2)^1.
                **
                **/
 
                or ((select max((abs(p.uid-u2.gid)*2) + ((p.protecttype/2)^1))
                        from sysprotects p, sysusers u2
                        where p.id = o.id      /* outer join to correlate
                                                ** with all rows in sysobjects
                                                */
			and u2.uid = user_id()
			/*
			** get rows for public, current users, user's groups
			*/
		      	and (p.uid = 0 or 		/* public */
			     p.uid = user_id() or	/* current user */ 
			     p.uid = u2.gid)		/* users group */ 

			/*
			** check for SELECT, EXECUTE privilege.
			*/
		 	and (p.action in (193,224)))&1

			/*
			** more magic...normalise GRANT
			** and final magic...compare
			** Grants.
			*/
			) = 1
		/*
		** If one of any user defined roles or contained roles for the
		** user has permission, the user has the permission
		*/
		or exists(select 1
			from sysprotects p1,
				master.dbo.syssrvroles srvro,
				sysroles ro
			where p1.id = o.id
			and p1.uid = ro.lrid
			and ro.id = srvro.srid
--	and has_role(srvro.name, 1) > 0
			and p1.action = 193))
		order by TABLE_TYPE, TABLE_CAT, TABLE_SCHEM, TABLE_NAME
	
end

go
exec sp_procxmode 'sp_odbc_tables', 'anymode'
go
grant execute on sp_odbc_tables to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go



if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_gettableprivileges')
begin
	drop procedure sp_odbc_gettableprivileges
end
go

/* Sccsid = "%Z% generic/sproc/src/%M% %I% %G%" */

create procedure sp_odbc_gettableprivileges ( 
                        @table_name  varchar(96),
                        @table_owner varchar(32) = null,
                        @table_qualifier varchar(32)= null)
as        
 
    declare @owner_id    		int
    declare @full_table_name    	varchar(193)
    declare @tab_id 			int	    /* object id of the table specified */

    declare @tab_name                   varchar(32)
    declare @tab_owner                  varchar(32)
    declare @table_id 			int	    /* object id of the
                                                       table specified */
    declare @startedInTransaction bit


    if (@@trancount > 0)
       select @startedInTransaction = 1
    else
       select @startedInTransaction = 0
       
    set nocount on
    /*
    ** set the transaction isolation level
    */
    if @@trancount = 0
    begin
	   set chained off
    end
    
    set transaction isolation level 1

    if (@startedInTransaction = 1)
	save transaction odbc_keep_temptable_tx      

    /*
    **  Check to see that the table is qualified with the database name
    */
    if @table_name like "%.%.%"
    begin
	/* 18021, "Object name can only be qualified with owner name." */
	raiserror 18021
	return (1)
    end

    /*  If this is a temporary table; object does not belong to 
    **  this database; (we should be in our temporary database)
    */
    if (@table_name like "#%" and db_name() != 'tempdb')
    begin
	/* 
	** 17676, "This may be a temporary object. Please execute 
	** procedure from your temporary database."
	*/
	raiserror 17676
	return (1)
    end


    /*
    ** The table_qualifier should be same as the database name. Do the sanity check
    ** if it is specified
    */
    if (@table_qualifier is null) or (@table_qualifier = '')
	/* set the table qualifier name */
	select @table_qualifier = db_name ()
    else
    begin
        if db_name() != @table_qualifier
        begin
	     /* 18039, "Table qualifier must be name of current database." */
	     raiserror 18039
	     return (1)
	end
    end
   
    /* 
    ** if the table owner is not specified, it will be taken as the id of the
    ** user executing this procedure. Otherwise find the explicit table name prefixed
    ** by the owner id
    */
    if (@table_owner is null) or (@table_owner = '')
        select @full_table_name = @table_name
    else
    begin
	if (@table_name like "%.%") and
	    substring (@table_name, 1, charindex(".", @table_name) -1) != @table_owner
	begin
	 	/* 18011, Object name must be qualified with the owner name */
		raiserror 18011
		return (1)
	end
	
	if not (@table_name like "%.%")
        	select @full_table_name = @table_owner + '.' + @table_name
	else
	        select @full_table_name = @table_name
    end

    /* 
    ** check to see if the specified table exists or not
    */

    select @tab_id = object_id(@full_table_name)
    if (@tab_id is null)
    begin
	/* 17492, "The table or view named doesn't exist in the current database." */
	raiserror 17492
	return (1)
    end


    /*
    ** check to see if the @tab_id indeeed represents a table or a view
    */

    if not exists (select * 
                  from   sysobjects
                  where (@tab_id = id) and
	                ((type = 'U') or
                        (type = 'S') or
		        (type = 'V')))
    begin
	/* 17492, "The table or view named doesn't exist in the current database." */
	raiserror 17492
	return (1)
    end

   /* 
   ** compute the table owner id
   */

    select @owner_id = uid
    from   sysobjects
    where  id = @tab_id



   /*
   ** get table owner name
   */

    select @table_owner = name 
    from sysusers 
    where uid = @owner_id

    /* Now, create a temporary table to hold a list of all the possible
       tables that we could get with the trio of table name, table owner and
       table catalog. Then, populate that table. */

    create table #odbc_tprivs
        (tab_id         int primary key not null,
         tab_name       varchar (32),
         tab_owner      varchar (32) null,
         uid            int,
         type           varchar (10))

    insert #odbc_tprivs 
        SELECT id, name, user_name(uid), uid, type 
        FROM sysobjects s 
        WHERE name LIKE @table_name ESCAPE '\'
            AND user_name (uid) LIKE @table_owner ESCAPE '\'
            AND charindex(substring(type,1,1), 'SUV') != 0

   /* Create temp table to store results from sp_aux_computeprivs */
    create table #results_table
	 (TABLE_CAT	varchar (32),
	  TABLE_SCHEM		varchar (32),
	  TABLE_NAME		varchar (32),
	  column_name		varchar (32) NULL,
	  GRANTOR		varchar (32),
	  GRANTEE 		varchar (32),
	  PRIVILEGE		varchar (32),
	  IS_GRANTABLE		varchar (3))

    declare tablepriv_cursor cursor for
        select tab_name, tab_owner, tab_id from #odbc_tprivs

    open tablepriv_cursor
   
    fetch tablepriv_cursor into @tab_name, @tab_owner, @table_id
 
    while (@@sqlstatus != 2)
    begin

        exec sp_odbc_computeprivs @tab_name, @tab_owner, @table_qualifier, 
			     NULL, 0, @table_id
        fetch tablepriv_cursor into @tab_name, @tab_owner, @table_id

    end

    close tablepriv_cursor
      /* Output the results table */

    select TABLE_CAT, TABLE_SCHEM, TABLE_NAME, GRANTOR, GRANTEE,
           PRIVILEGE, IS_GRANTABLE
    from #results_table
    order by TABLE_SCHEM, TABLE_NAME, PRIVILEGE

    drop table #odbc_tprivs
    drop table #results_table
  
    set nocount off 	
    if (@startedInTransaction = 1)
	rollback transaction odbc_keep_temptable_tx      

return (0)

go
exec sp_procxmode 'sp_odbc_gettableprivileges', 'anymode'
go
grant execute on sp_odbc_gettableprivileges to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_getindexinfo')
begin
	drop procedure sp_odbc_getindexinfo
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */

/*
** Messages for "sp_odbc_getindexinfo"          18039
**
** 18039, "Table qualifier must be name of current database."
** 18040, "Catalog procedure '%1!' can not be run in a transaction.
**
*/

/*
** Sp_statistics returns statistics for the given table, passed as first 
** argument. A row is returned for the table and then for each index found
** in sysindexes, starting with lowest value index id in sysindexes and 
** proceeding through the highest value index.  
**
** Returned rows consist of the columns:
** table qualifier (database name), table owner, table name from sysobjects, 
** non_unique (0/1), index qualifier (same as table name), 
** index name from sysindexes, type (SQL_INDEX_CLUSTERED/SQL_INDEX_OTHER), 
** sequence in index, column name, collation, table cardinality (row count), 
** and number of pages used by table (doampg).
*/

create procedure sp_odbc_getindexinfo (
	@table_name		varchar(96),
	@table_owner		varchar(32) = null,
	@table_qualifier	varchar(32) = null,
	@index_name		varchar(96) = '%',
	@is_unique 		char(1) = 'N')
as
declare @indid			int
declare @lastindid		int
declare @full_table_name	varchar(193)
declare @startedInTransaction bit

if (@@trancount > 0)
   select @startedInTransaction = 1
else
   select @startedInTransaction = 0

/*
** Verify table qualifier is name of current database.
*/
if @table_qualifier is not null
begin
	if db_name() != @table_qualifier
	begin	/* If qualifier doesn't match current database */
		/*
		** 18039, "Table qualifier must be name of current database."
		*/
		raiserror 18039
		return (1)
	end
end

if @@trancount = 0
begin
	set chained off
end

set transaction isolation level 1
if (@startedInTransaction = 1)
   save transaction odbc_keep_temptable_tx    


create table #TmpIndex(
	TABLE_CAT	varchar(32),
	TABLE_SCHEM	varchar(32),
	TABLE_NAME	varchar(32),
	INDEX_QUALIFIER varchar(32) null,
	INDEX_NAME	varchar(32) null,
	NON_UNIQUE	smallint null,
	TYPE		smallint,
	ORDINAL_POSITION	smallint null,
	COLUMN_NAME	varchar(32) null,
	ASC_OR_DESC	char(1) null,
	index_id	int null,
	CARDINALITY	int null,
	PAGES		int null,
	FILTER_CONDITION varchar(32) null,	
	status		smallint,
	status2		smallint)

/*
** Fully qualify table name.
*/
if @table_owner is null
begin	/* If unqualified table name */
	select @full_table_name = @table_name
end
else
begin	/* Qualified table name */
	select @full_table_name = @table_owner + '.' + @table_name
end

/*
** Start at lowest index id, while loop through indexes. 
** Create a row in #TmpIndex for every column in sysindexes, each is
** followed by an row in #TmpIndex with table statistics for the preceding
** index.
*/
select @indid = min(indid)
	from sysindexes
	where id = object_id(@full_table_name)
		and indid > 0
		and indid < 255

while @indid != NULL
begin
	insert #TmpIndex	/* Add all columns that are in index */
	select
		db_name(),		/* table_qualifier */
		user_name(o.uid),	/* table_owner	   */
		o.name,			/* table_name	   */
		o.name, 		/* index_qualifier */
		x.name,			/* index_name	   */
		0,			/* non_unique	   */
		1,			/* SQL_INDEX_CLUSTERED */
		colid,			/* seq_in_index	   */
		INDEX_COL(@full_table_name,indid,colid),/* column_name	   */
		index_colorder(@full_table_name,
			indid,colid),	/* collation	   */
		@indid,			/* index_id 	   */
	rowcnt(x.doampg),	/* cardinality	   */
--	row_count(db_id(), x.id), /* cardinality	*/	
	data_pgs(x.id,doampg),	/* pages	   */
--	data_pages(db_id(), x.id,
--		case
--			when x.indid = 1
--			then 0
--			else x.indid
--		end),	/* pages	   */
       		null,			/* Filter condition not available */
       					/* in SQL Server*/		
		x.status,		/* status	   */
		x.status2		/* status2	   */		
	from sysindexes x, syscolumns c, sysobjects o
	where x.id = object_id(@full_table_name)
		and x.id = o.id
		and x.id = c.id
		and c.colid < keycnt+(x.status&16)/16
		and x.indid = @indid

	/*
	** Save last index and increase index id to next higher value.
	*/
	select @lastindid = @indid
	select @indid = NULL

	select @indid = min(indid)
	from sysindexes
	where id = object_id(@full_table_name)
		and indid > @lastindid
		and indid < 255
end

update #TmpIndex
	set NON_UNIQUE = 1
	where status&2 != 2 /* If non-unique index */

update #TmpIndex
	set
		TYPE = 3,		/* SQL_INDEX_OTHER */
		CARDINALITY = NULL,
		PAGES = NULL
	where index_id > 1		/* If non-clustered index */

update #TmpIndex
	set TYPE = 1			/* SQL_INDEX_CLUSTERED */
	where 
	status2&512 = 512	/* if placement index */
/* 
** Now add row with table statistics 
*/
insert #TmpIndex
	select
		db_name(),			/* table_qualifier */
		user_name(o.uid),		/* table_owner	   */
		o.name, 			/* table_name	   */
		null,				/* index_qualifier */
		null,				/* index_name	   */
		null,				/* non_unique	   */
		0,				/* SQL_table_STAT  */
		null,				/* seq_in_index	*/
		null,				/* column_name	   */
		null,				/* collation	   */
		0,				/* index_id 	   */
	rowcnt(x.doampg),	/* cardinality	   */
--	row_count(db_id(), x.id), /* cardinality	*/	
	data_pgs(x.id,doampg),	/* pages	   */
--	data_pages(db_id(), x.id,
--		case
--			when x.indid = 1
--			then 0
--			else x.indid
--		end),		/* pages	   */
       		null,				/* Filter condition not available */
        					/* in SQL Server*/		
		0,				/* status	   */
		0				/* status2	   */
	from sysindexes x, sysobjects o
	where o.id = object_id(@full_table_name)
		and x.id = o.id
		and (x.indid = 0 or x.indid = 1)	
	/*  
	** If there are no indexes
	** then table stats are in a row with indid = 0
	*/

if @is_unique != 'Y'	
begin
	/* If all indexes desired */
	select
		TABLE_CAT,
		TABLE_SCHEM,
		TABLE_NAME,
		NON_UNIQUE,
		INDEX_QUALIFIER,
		INDEX_NAME,
		TYPE,
		ORDINAL_POSITION,
		COLUMN_NAME,
		ASC_OR_DESC,
		CARDINALITY,
		PAGES,
		FILTER_CONDITION
	from #TmpIndex
	where INDEX_NAME like @index_name 	/* If matching name */
		or INDEX_NAME is null		/* If SQL_table_STAT row */
	order by NON_UNIQUE, TYPE, INDEX_NAME, ORDINAL_POSITION
end
else	
begin
	/* else only unique indexes desired */
	select
		TABLE_CAT,
		TABLE_SCHEM,
		TABLE_NAME,
		NON_UNIQUE,
		INDEX_QUALIFIER,
		INDEX_NAME,
		TYPE,
		ORDINAL_POSITION,
		COLUMN_NAME,
		ASC_OR_DESC,
		CARDINALITY,
		PAGES,
		FILTER_CONDITION
	from #TmpIndex
	where (NON_UNIQUE = 0 			/* If unique */
		or NON_UNIQUE is NULL)		/* If SQL_table_STAT row */
		and (INDEX_NAME like @index_name	/* If matching name */
		or INDEX_NAME is NULL)		/* If SQL_table_STAT row */
	order by NON_UNIQUE, TYPE, INDEX_NAME, ORDINAL_POSITION

end

drop table #TmpIndex
if (@startedInTransaction = 1)
   rollback transaction odbc_keep_temptable_tx      

return (0)
go
exec sp_procxmode 'sp_odbc_getindexinfo', 'anymode'
go
grant execute on sp_odbc_getindexinfo to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_primarykey')
begin
	drop procedure sp_odbc_primarykey
end
go

/* Sccsid = "%Z% generic/sproc/src/%M% %I% %G%" */
/*
** note: there is one raiserror message: 18040
**
** messages for "sp_odbc_primarykey"               18039, 18040
**
** 17461, "Object does not exist in this database."
** 18039, "table qualifier must be name of current database."
** 18040, "catalog procedure %1! can not be run in a transaction.", sp_odbc_primarykey
**
*/

create procedure sp_odbc_primarykey
			   @table_name		varchar(96),
			   @table_owner 	varchar(32) = null,
			   @table_qualifier varchar(32) = null 
as
declare @keycnt smallint
declare @indexid smallint
declare @indexname varchar(96)
declare @i int
declare @id int
declare @uid int
declare @startedInTransaction bit
if (@@trancount > 0)
   select @startedInTransaction = 1
else
   select @startedInTransaction = 0
   
   
select @id = NULL


	set nocount on

if (@@trancount = 0)
begin
   set chained off
end

 if (@startedInTransaction = 1)
    save transaction odbc_keep_temptable_tx    



	set transaction isolation level 1

	if @table_qualifier is not null
	begin
		if db_name() != @table_qualifier
		begin	
			/* if qualifier doesn't match current database */
			/* "table qualifier must be name of current database"*/
			raiserror 18039
			return (1)
		end
	end

	if @table_owner is null
	begin
		select @id = id , @uid = uid
		from sysobjects 
		where name = @table_name
			and uid = user_id()
		if (@id is null)
		begin
			select @id = id ,@uid = uid
			from sysobjects 
			where name = @table_name
			and uid = 1
		end
	end
	else
	begin
		select @id = id , @uid = uid
		from sysobjects 
		where name = @table_name and uid = user_id(@table_owner)
	end
	
	if (@id is null)
	begin	
		/* 17461, "Object does not exist in this database." */
		raiserror 17461
		return (1)
	end

	create table #pkeys(
			 TABLE_CAT varchar(32),
			 TABLE_SCHEM     varchar(32),
			 TABLE_NAME      varchar(32),
			 COLUMN_NAME     varchar(32),
			 KEY_SEQ	 smallint,
			 PK_NAME     	 varchar(32))


/*
**  now we search for primary key (only declarative) constraints
**  There is only one primary key per table.
*/

	select @keycnt = keycnt, @indexid = indid ,@indexname=name
	from   sysindexes
	where  id = @id
	and indid > 0 /* make sure it is an index */
	and status2 & 2 = 2 /* make sure it is a declarative constr */
	and status & 2048 = 2048 /* make sure it is a primary key */

/*
**  For non-clustered indexes, keycnt as returned from sysindexes is one
**  greater than the actual key count. So we need to reduce it by one to
**  get the actual number of keys.
*/

	if (@indexid >= 2)
	begin
		select @keycnt = @keycnt - 1
	end

	select @i = 1

	while @i <= @keycnt
	begin
		insert into #pkeys values
		(db_name(), user_name(@uid), @table_name,
			index_col(@table_name, @indexid, @i, @uid), @i,@indexname)
		select @i = @i + 1
	end

	select TABLE_CAT, TABLE_SCHEM, TABLE_NAME, COLUMN_NAME, KEY_SEQ, PK_NAME
	from #pkeys
	order by TABLE_CAT, TABLE_SCHEM, TABLE_NAME, KEY_SEQ
	
 drop table #pkeys	
 if (@startedInTransaction = 1)
    rollback transaction odbc_keep_temptable_tx    
	
return (0)
go
exec sp_procxmode 'sp_odbc_primarykey', 'anymode'
go
grant execute on sp_odbc_primarykey to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go
if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_fkeys')
begin
	drop procedure sp_odbc_fkeys
end
go

/* sccsid = "%Z% generic/sproc/src/%M% %I% %G%" */
/*
** note: there is one raiserror message: 18040
**
** messages for "sp_odbc_fkeys"               18039, 18040
**
** 17461, "Object does not exist in this database." 
** 18040, "Catalog procedure %1! can not be run in a transaction.", sp_odbc_fkeys
** 18043 " Primary key table name or foreign key table name or both must be 
** given"
** 18044, "%1! table qualifier must be name of current database." [Primary
** key | Foreign key]
**
*/
CREATE PROCEDURE sp_odbc_fkeys
			   @pktable_name		varchar(32) = null,
			   @pktable_owner		varchar(32) = null,
			   @pktable_qualifier	varchar(32) = null,
			   @fktable_name		varchar(32) = null,
			   @fktable_owner		varchar(32) = null,
			   @fktable_qualifier	varchar(32) = null 
as
declare @ftabid int, @ptabid int, @constrid int,@keycnt int, @i int
declare @fokey1 int,  @fokey2 int,  @fokey3 int,  @fokey4 int,  @fokey5  int
declare @fokey6 int,  @fokey7 int,  @fokey8 int,  @fokey9 int,  @fokey10 int
declare @fokey11 int, @fokey12 int, @fokey13 int, @fokey14 int, @fokey15 int
declare @refkey1 int, @refkey2 int, @refkey3 int, @refkey4 int, @refkey5  int
declare @refkey6 int, @refkey7 int, @refkey8 int, @refkey9 int, @refkey10 int
declare @refkey11 int, @refkey12 int, @refkey13 int, @refkey14 int
declare @refkey15 int, @refkey16 int, @fokey16 int, @status int
declare @msg varchar(255)
declare @msg2 varchar(255)
declare @ordpkey	int
declare @notDeferrable smallint
declare @startedInTransaction bit
	if (@@trancount > 0)
	   select @startedInTransaction = 1
	else
	   select @startedInTransaction = 0

	set nocount on

	if (@@trancount = 0)
	begin
		set chained off
	end

	set transaction isolation level 1

	if (@startedInTransaction = 1)
	    save transaction odbc_keep_temptable_tx    
	
	select @notDeferrable = 7

	if (@pktable_name is null) and (@fktable_name is null)
	begin	
		/* If neither primary key nor foreign key table names given */
		/* 
		** 18043 "Primary key table name or foreign key table name 
		** or both must be given"
		*/
		raiserror 18043
		return (1)
	end

	if @fktable_qualifier is not null
	begin
		if db_name() != @fktable_qualifier
		begin	
			/* If qualifier doesn't match current database */
			/* 18044 "%1! Table qualifier must be name of current database"
			** 18050 "Foreign key"
			*/
			exec sp_getmessage 18050, @msg2 output
			raiserror 18044, @msg2
			return (1)
		end
	end
	else
	begin
		/*
		** Now make sure that foreign table qualifier is pointing to the
		** current database in case it is not specified.
		*/
		select @fktable_qualifier = db_name()
	end

	if @pktable_qualifier is not null
	begin
		if db_name() != @pktable_qualifier
		begin	
			/* If qualifier doesn't match current database */
			/* 18044 "%1! Table qualifier must be name of current database"
			** 18051 "Primary Key"
			*/
			exec sp_getmessage 18051, @msg2 output
			raiserror 18044, @msg2
			return (1)
		end
	end
	else
	begin
		/*
		** Now make sure that primary table qualifier is pointing to the
		** current database in case it is not specified.
		*/
		select @pktable_qualifier = db_name()
	end


	create table #opid (pid int, uid int, name varchar(32))
	create table #ofid (fid int, uid int, name varchar(32))

	/* we will sort by fkey		*/
	/* unless pktable is null	*/

	select @ordpkey = 0

	if @pktable_name is not null
	begin 

		if (@pktable_owner is null)
		begin
			/* 
			** owner is NULL, so default to the current user
			** who owns this table, otherwise default to dbo
			** who owns this table.
			*/
			insert into #opid 
			select id, uid, name
			from sysobjects 
			where name = @pktable_name and uid = user_id()
			and type in ("S", "U")
			
			/* 
			** If the current user does not own the table, see
			** if the DBO of the current database owns the table.
			*/

			if ((select count(*) from #opid ) = 0)
			begin
				insert into #opid 
				select id, uid, name
				from sysobjects 
				where name = @pktable_name and uid = 1
				and type in ("S", "U")
			end
		end
		else
		begin
			insert into #opid
			select id, uid, name
			from sysobjects
			where name = @pktable_name 
			and uid = user_id(@pktable_owner)
			and type in ("S", "U")
		end
	end
	else 
	begin
		if (@pktable_owner is null)
		begin
		/* 
		** If neither pktable_name nor pktable_owner is specified,
		** then we are interested in every user or system table.
		*/
			insert into #opid 
			select id, uid, name
			from sysobjects 
			where type in ("S", "U")
		end
		else
		begin
			insert into #opid
			select id, uid, name
			from sysobjects
			where  uid = user_id(@pktable_owner)
			and type in ("S", "U")
		end
	end
		
	if @fktable_name is not null
	begin 
		/* sort by pkey	*/
		select @ordpkey = 1

		if (@fktable_owner is null)
		begin
			/* 
			** owner is NULL, so default to the current user
			** who owns this table, otherwise default to dbo
			** who owns this table.
			*/
			insert into #ofid 
			select id, uid, name
			from sysobjects 
			where name = @fktable_name and uid = user_id()
			and type in ("S", "U")

			/* 
			** If the current user does not own the table, see
			** if the DBO of the current database owns the table.
			*/

			if ((select count(*) from #opid ) = 0)
			begin
				insert into #ofid 
				select id, uid, name
				from sysobjects 
				where name = @fktable_name and uid = 1
				and type in ("S", "U")
			end
		end
		else
		begin
			insert into #ofid
			select id, uid, name
			from sysobjects
			where name = @fktable_name 
			and uid = user_id(@fktable_owner)
			and type in ("S", "U")
		end
	end
	else
	begin
		if (@fktable_owner is null)
		begin
		/* 
		** If neither fktable_name nor fktable_owner is specified,
		** then we are interested in every user table or systme 
		** table.
		*/			
			insert into #ofid 
			select id, uid, name
			from sysobjects 
			where type in ("S", "U")
		end
		else
		begin
			insert into #ofid
			select id, uid, name
			from sysobjects
			where  uid = user_id(@fktable_owner)
			and type in ("S", "U")
		end
	end

	if (((select count(*) from #ofid ) = 0) or
		((select count(*) from #opid) = 0))
	begin
		/* 17461, "Object does not exist in this database." */
		raiserror 17461
		return (1)
	end

	create table #ofkey_res( PKTABLE_CAT varchar(32),
				PKTABLE_SCHEM       varchar(32),
				PKTABLE_NAME       varchar(32),
				PKCOLUMN_NAME      varchar(32),
				FKTABLE_CAT varchar(32),
				FKTABLE_SCHEM       varchar(32),
				FKTABLE_NAME       varchar(32),
				FKCOLUMN_NAME       varchar(32),
				KEY_SEQ           smallint,	
				UPDATE_RULE smallint, 
				DELETE_RULE smallint,
				FK_NAME	varchar(32),
				PK_NAME	varchar(32))
	create table #opkeys(seq int,  keys varchar(32) null)
	create table #ofkeys(seq int, keys varchar(32) null)

	/*
	** Since there are possibly multiple rows in sysreferences
	** that describe foreign and primary key relationships among
	** two tables, so we declare a cursor on the selection from
	** sysreferences and process the output at row by row basis.
	*/
		
	declare curs_sysreferences cursor
	for
	select tableid, reftabid, constrid, keycnt,
	fokey1, fokey2, fokey3, fokey4, fokey5, fokey6, fokey7, fokey8, 
	fokey9, fokey10, fokey11, fokey12, fokey13, fokey14, fokey15,
	fokey16, refkey1, refkey2, refkey3, refkey4, refkey5,
	refkey6, refkey7, refkey8, refkey9, refkey10, refkey11,
	refkey12, refkey13, refkey14, refkey15, refkey16
	from sysreferences
	where tableid in (
		select fid from #ofid)
	and reftabid in (
		select pid from #opid)
	and frgndbname is NULL and pmrydbname is NULL
	for read only

	open  curs_sysreferences

	fetch  curs_sysreferences into @ftabid, @ptabid, @constrid, @keycnt,@fokey1, 
	@fokey2, @fokey3,  @fokey4, @fokey5, @fokey6, @fokey7, @fokey8, 
	@fokey9, @fokey10, @fokey11, @fokey12, @fokey13, @fokey14, @fokey15, 
	@fokey16, @refkey1, @refkey2, @refkey3, @refkey4, @refkey5, @refkey6, 
	@refkey7, @refkey8, @refkey9, @refkey10, @refkey11, @refkey12, 
	@refkey13, @refkey14, @refkey15, @refkey16

	while (@@sqlstatus = 0)
	begin
		/*
		** For each row of sysreferences which describes a foreign-
		** primary key relationship, do the following.
		*/

		/*
		** First store the column names that belong to primary keys
		** in table #pkeys for later retrieval.
		*/

		delete #opkeys
		insert #opkeys values(1, col_name(@ptabid,@refkey1))
		insert #opkeys values(2, col_name(@ptabid,@refkey2))
		insert #opkeys values(3, col_name(@ptabid,@refkey3))
		insert #opkeys values(4, col_name(@ptabid,@refkey4))
		insert #opkeys values(5, col_name(@ptabid,@refkey5))
		insert #opkeys values(6, col_name(@ptabid,@refkey6))
		insert #opkeys values(7, col_name(@ptabid,@refkey7))
		insert #opkeys values(8, col_name(@ptabid,@refkey8))
		insert #opkeys values(9, col_name(@ptabid,@refkey9))
		insert #opkeys values(10, col_name(@ptabid,@refkey10))
		insert #opkeys values(11, col_name(@ptabid,@refkey11))
		insert #opkeys values(12, col_name(@ptabid,@refkey12))
		insert #opkeys values(13, col_name(@ptabid,@refkey13))
		insert #opkeys values(14, col_name(@ptabid,@refkey14))
		insert #opkeys values(15, col_name(@ptabid,@refkey15))
		insert #opkeys values(16, col_name(@ptabid,@refkey16))
	
		/*
		** Second store the column names that belong to foreign keys
		** in table #fkeys for later retrieval.
		*/
		
		delete #ofkeys
		insert #ofkeys values(1, col_name(@ftabid,@fokey1))
		insert #ofkeys values(2, col_name(@ftabid,@fokey2))
		insert #ofkeys values(3, col_name(@ftabid,@fokey3))
		insert #ofkeys values(4, col_name(@ftabid,@fokey4))
		insert #ofkeys values(5, col_name(@ftabid,@fokey5))
		insert #ofkeys values(6, col_name(@ftabid,@fokey6))
		insert #ofkeys values(7, col_name(@ftabid,@fokey7))
		insert #ofkeys values(8, col_name(@ftabid,@fokey8))
		insert #ofkeys values(9, col_name(@ftabid,@fokey9))
		insert #ofkeys values(10, col_name(@ftabid,@fokey10))
		insert #ofkeys values(11, col_name(@ftabid,@fokey11))
		insert #ofkeys values(12, col_name(@ftabid,@fokey12))
		insert #ofkeys values(13, col_name(@ftabid,@fokey13))
		insert #ofkeys values(14, col_name(@ftabid,@fokey14))
		insert #ofkeys values(15, col_name(@ftabid,@fokey15))
		insert #ofkeys values(16, col_name(@ftabid,@fokey16))
	
		/* 
		** For each column of the current foreign-primary key relation,
		** create a row into result table: #fkey_res.
		*/

		select @i = 1
		while (@i <= @keycnt)
		begin
			insert into #ofkey_res 
				select @pktable_qualifier,
				(select user_name(uid) from #opid where pid = @ptabid),
				object_name(@ptabid),
				(select keys from #opkeys where seq = @i),
				@fktable_qualifier,
				(select user_name(uid) from #ofid where fid = @ftabid),
				object_name(@ftabid), 
				(select keys from #ofkeys where seq = @i),@i,
				1, 1,
			/* Foreign Key */				
				object_name(@constrid),
			/* Primary key name */
		                (select name from sysindexes where id = @ptabid
		                    and status > 2048 and status < 32768)
			select @i = @i + 1
		end
		
		/* 
		** Go to the next foreign-primary key relationship if any.
		*/

		fetch  curs_sysreferences into @ftabid, @ptabid, @constrid, @keycnt,@fokey1, 
		@fokey2, @fokey3,  @fokey4, @fokey5, @fokey6, @fokey7, @fokey8, 
		@fokey9, @fokey10, @fokey11, @fokey12, @fokey13, @fokey14, @fokey15, 
		@fokey16, @refkey1, @refkey2, @refkey3, @refkey4, @refkey5, @refkey6, 
		@refkey7, @refkey8, @refkey9, @refkey10, @refkey11, @refkey12, 
		@refkey13, @refkey14, @refkey15, @refkey16
	end

	close curs_sysreferences
	deallocate cursor curs_sysreferences

	/*
	** Everything is now in the result table #fkey_res, so go ahead
	** and select from the table now.
	*/

	/* if @ordpkey = 0 sort by fkey */
	/* else sort by pkey		*/
	if @ordpkey = 0
	begin
		select PKTABLE_CAT, PKTABLE_SCHEM, PKTABLE_NAME,
		PKCOLUMN_NAME, FKTABLE_CAT, FKTABLE_SCHEM, 
		FKTABLE_NAME, FKCOLUMN_NAME, KEY_SEQ, UPDATE_RULE, DELETE_RULE,
		FK_NAME,PK_NAME,@notDeferrable as DEFERRABILITY
		from #ofkey_res
		order by FKTABLE_NAME,FKTABLE_SCHEM,KEY_SEQ, FKTABLE_CAT
	end
	else
	begin
		select PKTABLE_CAT, PKTABLE_SCHEM, PKTABLE_NAME,
		PKCOLUMN_NAME, FKTABLE_CAT, FKTABLE_SCHEM, 
		FKTABLE_NAME, FKCOLUMN_NAME, KEY_SEQ, UPDATE_RULE, DELETE_RULE,
		FK_NAME,PK_NAME,@notDeferrable as DEFERRABILITY
		from #ofkey_res
		order by PKTABLE_NAME,PKTABLE_SCHEM,KEY_SEQ, PKTABLE_CAT
	end

drop table #opkeys
drop table #ofkeys
drop table #ofkey_res
if (@startedInTransaction = 1)
    rollback transaction odbc_keep_temptable_tx	
	
go
exec sp_procxmode 'sp_odbc_fkeys', 'anymode'
go
grant execute on sp_odbc_fkeys to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go


if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_stored_procedures')
begin
	drop procedure sp_odbc_stored_procedures
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */

/*
** Messages for "sp_odbc_stored_procedures"	18041
**
** 18041, "Stored Procedure qualifier must be name of current database."
**
*/
create procedure sp_odbc_stored_procedures
@sp_name	varchar(96) = null,	/* stored procedure name */
@sp_owner	varchar(32) = null,	/* stored procedure owner */
@sp_qualifier	varchar(32) = null	/* stored procedure qualifier; 
					** For the SQL Server, the only valid
					** values are NULL or the current 
					** database name
					*/
as


if @@trancount = 0
begin
	set chained off
end

set transaction isolation level 1

/* If qualifier is specified */
if @sp_qualifier is not null
begin
	/* If qualifier doesn't match current database */
	if db_name() != @sp_qualifier
	begin
		/* If qualifier is not specified */
		if @sp_qualifier = ''
		begin
			/* in this case, we need to return an empty 
			** result set because the user has requested a 
			** database with an empty name 
			*/
			select @sp_name = ''
			select @sp_owner = ''
		end

		/* qualifier is specified and does not match current database */
		else
		begin	
			/* 
			** 18041, "Stored Procedure qualifer must be name of
			** current database"
			*/
			raiserror 18041
			return (1)
		end
	end
end

/* If procedure name not supplied, match all */
if @sp_name is null
begin  
	select @sp_name = '%'
end
else 
begin
	/* If owner name is not supplied, but procedure name is */ 
	if (@sp_owner is null) and (charindex('%', @sp_name) = 0)
	begin
		/* If procedure exists and is owned by the current user */
		if exists (select * 
			   from sysobjects
			   where uid = user_id()
				and name = @sp_name
				and type = 'P') /* Object type of Procedure */
		begin
			/* Set owner name to current user */
			select @sp_owner = user_name()
		end
	end
end

/* If procedure owner not supplied, match all */
if @sp_owner is null	
	select @sp_owner = '%'

/* 
** Retrieve the stored procedures and associated info on them
*/
select  PROCEDURE_CAT = db_name(),
	PROCEDURE_SCHEM = user_name(o.uid),
	PROCEDURE_NAME = o.name ,
	NUM_INPUT_PARAMS = -1,		/* Constant since value unknown */
	NUM_OUTPUT_PARAMS = -1, 	/* Constant since value unknown */
	NUM_RESULT_SETS = -1,		/* Constant since value unknown */
	REMARKS = convert(varchar(254),null),	/* Remarks are NULL */
	PROCEDURE_TYPE = case when o.type='P' then convert(smallint, 1) when o.type='F' then convert(smallint, 2) end
from sysobjects o,sysprocedures p,sysusers u
where o.name like @sp_name
	and p.sequence = 0
	and user_name(o.uid) like @sp_owner
	and o.type in ('P','F')		/* Object type of Procedure or Function */
	and p.id = o.id
	and u.uid = user_id()		/* constrain sysusers uid for use in 
					** subquery 
					*/

	and (suser_id() = 1 		/* User is the System Administrator */
	     or  o.uid = user_id()	/* User created the object */
					/* here's the magic..select the highest 
					** precedence of permissions in the 
					** order (user,group,public)  
					*/

	     /*
	     ** The value of protecttype is
	     **
	     **		0  for grant with grant
	     **		1  for grant and,
	     **		2  for revoke
	     **
	     ** As protecttype is of type tinyint, protecttype/2 is
	     ** integer division and will yield 0 for both types of
	     ** grants and will yield 1 for revoke, i.e., when
	     ** the value of protecttype is 2.  The XOR (^) operation
	     ** will reverse the bits and thus (protecttype/2)^1 will
	     ** yield a value of 1 for grants and will yield a
	     ** value of zero for revoke.
	     **
	     ** For groups, uid = gid. We shall use this to our advantage.
             ** 	
	     ** If there are several entries in the sysprotects table
	     ** with the same Object ID, then the following expression
	     ** will prefer an individual uid entry over a group entry
	     **
	     ** For example, let us say there are two users u1 and u2
	     ** with uids 4 and 5 respectiveley and both u1 and u2
	     ** belong to a group g12 whose uid is 16390.  procedure p1
	     ** is owned by user u0 and user u0 performs the following
	     ** actions:
	     **
	     **		grant exec on p1 to g12
	     **		revoke grant on p1 from u1
	     **
	     ** There will be two entries in sysprotects for the object
	     ** p1, one for the group g12 where protecttype = grant (1)
	     ** and one for u1 where protecttype = revoke (2).
	     **
	     ** For the group g12, the following expression will
	     ** evaluate to:
	     **
	     **		((abs(16390-16390)*2) + ((1/2)^1))
	     **		= ((0) + (0)^1) = 0 + 1 = 1
	     **
	     ** For the user entry u1, it will evaluate to:
	     **
	     **		((abs(4-16390)*2) + ((2/2)^1))
	     **		= ((abs(-16386)*2 + (1)^1)
	     **		= 16386*2 + 0 = 32772 
	     **
	     ** As the expression evaluates to a bigger number for the
	     ** user entry u1, select max() will chose 32772 which,
	     ** ANDed with 1 gives 0, i.e., sp_odbc_stored_procedures will
	     ** not display this particular procedure to the user.
	     **
	     ** When the user u2 invokes sp_odbc_stored_procedures, there is
	     ** only one entry for u2, which is the entry for the group
	     ** g12, and so this entry will be selected thus allowing
	     ** the procedure in question to be displayed.
	     **
             ** NOTE: With the extension of the uid's into negative space, 
             ** and uid limits going beyond 64K, the original expression 
	     ** has been modified from
	     ** ((select max(((sign(uid)*abs(uid-16383))*2)
	     **		+ ((protecttype/2)^1))
	     ** to
	     ** ((select max((abs(uid-u.gid)*2)
	     **		+ ((protecttype/2)^1))
	     ** 
	     ** Notice that multiplying by 2 makes the number an
	     ** even number (meaning the last digit is 0) so what
	     ** matters at the end is (protecttype/2)^1.
	     **
	     */

	     or ((select distinct  max( (abs(p.uid-u2.gid)*2) + ((p.protecttype/2)^1))
		   from sysprotects p, sysusers u2
		   where p.id = o.id
		   and u2.uid = user_id()
		   /*
		   ** get rows for public, current users, user's groups
		   */
		   and (p.uid = 0  		/* get rows for public */
		        or p.uid = user_id()	/* current user */
		        or p.uid = u2.gid) 	/* users group */
			     
		   /*
		   ** check for SELECT, EXECUTE privilege.
		   */
	           and (p.action in (193,224))	/* check for SELECT,EXECUTE 
						** privilege 
						*/
		   )&1 			/* more magic...normalize GRANT */
	    	  ) = 1	 		/* final magic...compare Grants	*/
	     /*
	     ** If one of any user defined roles or contained roles for the
	     ** user has permission, the user has the permission
	     */
	     or exists(select 1
		from	sysprotects p1,
			master.dbo.syssrvroles srvro,
			sysroles ro
		where	p1.id = o.id
			and p1.uid = ro.lrid
			and ro.id = srvro.srid
--	and has_role(srvro.name, 1) > 0	
			and p1.action = 224))
			
order by PROCEDURE_CAT, PROCEDURE_SCHEM, PROCEDURE_NAME
go
exec sp_procxmode 'sp_odbc_stored_procedures', 'anymode'
go
grant execute on sp_odbc_stored_procedures to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go

if exists (select *
	from sysobjects
		where sysstat & 7 = 4
			and name = 'sp_odbc_getprocedurecolumns')
begin
	drop procedure sp_odbc_getprocedurecolumns
end
go

/* Sccsid = "%Z% generic/sproc/%M% %I% %G%" */

/*
** Messages for "sp_odbc_getprocedurecolumns"
**
** 18039, "Table qualifier must be name of current database"
*/

create procedure sp_odbc_getprocedurecolumns
@procedure_name		varchar(96) = '%', 	/* name of stored procedure  */
@procedure_owner 	varchar(32) = null,	/* owner of stored procedure */
@procedure_qualifier	varchar(32) = null,	/* name of current database  */
@column_name		varchar(96) = null	/* col name or param name    */
as

declare @msg 		  varchar(32)
declare @group_num		int
declare @semi_position		int
declare @full_procedure_name	varchar(193)
declare @procedure_id		int
declare @char_bin_types   varchar(32) 
declare @sptlang 			int

if @@trancount = 0
begin
	set chained off
end

set transaction isolation level 1

 select @sptlang = @@langid

 if @@langid != 0
 begin
         if not exists (
                 select * from master.dbo.sysmessages where error
                 between 17100 and 17109
                 and langid = @@langid)
             select @sptlang = 0
 end

/* If column name not supplied, match all */
if @column_name is null 
	select @column_name = '%'

/* The qualifier must be the name of current database or null */
if @procedure_qualifier is not null
begin
	if db_name() != @procedure_qualifier
	begin
	if @procedure_qualifier = ''
		begin
			/* in this case, we need to return an empty result 
			** set because the user has requested a database with
			** an empty name
			*/
			select @procedure_name = ''
			select @procedure_owner = ''
		end
		else
		begin
			/*
			** 18039, Table qualifier must be name of current database
			*/
			exec sp_getmessage 18039, @msg output
			print @msg
			return
		end
	end
end


/* first we need to extract the procedure group number, if one exists */
select @semi_position = charindex(';',@procedure_name)
if (@semi_position > 0)
begin	/* If group number separator (;) found */
	select @group_num = convert(int,substring(@procedure_name, 
						  @semi_position + 1, 2))
	select @procedure_name = substring(@procedure_name, 1, 
					   @semi_position -1)
end
else
begin	/* No group separator, so default to group number of 1 */
	select @group_num = 1
end

/* character and binary datatypes */
select @char_bin_types =
	char(47)+char(39)+char(45)+char(37)+char(35)+char(34)

if @procedure_owner is null
begin	/* If unqualified procedure name */
	select @full_procedure_name = @procedure_name
end
else
begin	/* Qualified procedure name */
	select @full_procedure_name = @procedure_owner + '.' + @procedure_name
end

/*
** If the @column_name parameter is "RETURN_VALUE" and this is a sqlj
** function, then we should be looking for column name "Return Type"
*/
if @column_name = "RETURN_VALUE"
	and exists (select 1 from sysobjects
		    where id = object_id(@full_procedure_name)
		    and type = 'F')
begin	
	select @column_name = "Return Type"
end

/*	Get Object ID */
select @procedure_id = object_id(@full_procedure_name)

if ((charindex('%',@full_procedure_name) = 0) and
	(charindex('_',@full_procedure_name) = 0)  and
	@procedure_id != 0)
begin
/*
** this block is for the case where there is no pattern
** matching required for the table name
*/
	select	/* INTn, FLOATn, DATETIMEn and MONEYn types */
		PROCEDURE_CAT = db_name(),
		PROCEDURE_SCHEM = user_name(o.uid),
		PROCEDURE_NAME = o.name ,
                COLUMN_NAME =
                        case
                            when c.name = 'Return Type' then 'RETURN_VALUE'
                            else c.name
                        end,
                COLUMN_TYPE =
		case
			when c.name = 'Return Type'
				then convert(smallint, 5)
--		when c.status2 = 1
--			then convert(smallint, 1)
--		when c.status2 = 2
--			then convert(smallint, 4)
--		when c.status2 = 4			     		
--			then  convert(smallint, 2)
		else convert(smallint, 0)
		end,

/*
** With the current data in the spt_datatype_info table, the convert() below
** is never being used.
** These conversions were ported from the original Microsoft INSTCAT.SQL
** file which contained catalog stored procedures for 4.9 and earlier SQL
** Servers.
*/
		DATA_TYPE = 
		case 
			when d.data_type = 11
				then convert(smallint,93)
		else
			d.data_type
			    +convert(smallint, 
				     isnull(d.aux,
					    ascii(substring("666AAA@@@CB??GG",
						            2*(d.ss_dtype%35+1)
							    +2-8/c.length,
							    1)) - 60))
		end,
		TYPE_NAME = rtrim(substring(d.type_name,
					1+isnull(d.aux,
					     ascii(substring("III<<<MMMI<<A<A",
							2*(d.ss_dtype%35+1)
							+2-8/c.length,
						        1)) - 60), 
					    18)),
		COLUMN_SIZE = isnull(convert(int, c.prec),
			isnull(d.data_precision, convert(int,c.length)))
			     +isnull(d.aux, convert(int,
					     ascii(substring("???AAAFFFCKFOLS",
						          2*(d.ss_dtype%35+1)
							  +2-8/c.length,1))
							  -60)),
		BUFFER_LENGTH = isnull(d.length, convert(int,c.length))
			 +convert(int, isnull(d.aux,
					     ascii(substring("AAA<BB<DDDHJSPP",
						    	     2*(d.ss_dtype%35
							     +1)+2-8/c.length,
						             1))-64)),
		DECIMAL_DIGITS = isnull(convert(smallint, c.scale),
			convert(smallint, d.numeric_scale)) +
			convert(smallint, 
				isnull(d.aux, ascii(substring("<<<<<<<<<<<<<<?",
					        2*(d.ss_dtype%35+1)
						+2-8/c.length,
					        1))-60)),
		NUM_PREC_RADIX = d.numeric_radix,
		NULLABLE =	/* set nullability from status flag */
			convert(smallint,1),/*convert(smallint, convert(bit, c.status&8))*/
		REMARKS = convert(varchar(254),NULL),	/* Remarks are NULL */
		COLUMN_DEF = convert(varchar(254),NULL),
		SQL_DATA_TYPE = isnull(d.sql_data_type,
			d.data_type+convert(smallint,
			isnull(d.aux,
			ascii(substring("666AAA@@@CB??GG",
			2*(d.ss_dtype%35+1)+2-8/c.length,1))
			-60))),
		SQL_DATETIME_SUB = NULL,
		CHAR_OCTET_LENGTH = 
		case 
			when d.data_type = 4 then convert(smallint,NULL)
		else
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision
		** if not, return a 0 and multiply it by the precision
		*/
			convert(smallint,
		    	substring('0111111',
			charindex(char(c.type),
			@char_bin_types)+1, 1)) *
			/* calculate the precision */
			isnull(convert(int, c.prec),
		    	isnull(convert(int, d.data_precision),
			convert(int, c.length)))
		   	 +isnull(d.aux, convert(int,
			ascii(substring('???AAAFFFCKFOLS',
			   2*(d.ss_dtype%35+1)+2-8/c.length,1))-60))
		end,
		ORDINAL_POSITION = convert(int,c.colid),
		IS_NULLABLE = 'YES'
			/* rtrim(substring('NO YES',
			(convert(smallint, convert(bit, c.status&8))*3)+1, 3))*/
	from
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t,
		sysprocedures p
	where
		o.id = @procedure_id
		and c.id = o.id
		and c.type = d.ss_dtype
		and c.name like @column_name
		and d.ss_dtype in (111, 109, 38, 110)	/* Just *N types */
		and c.number = @group_num
	union
	select
		PROCEDURE_CAT = db_name(),
		PROCEDURE_SCHEM = user_name(o.uid),
		PROCEDURE_NAME = o.name ,
		COLUMN_NAME = 'RETURN_VALUE',
		COLUMN_TYPE = convert(smallint, 5), /* return parameter */
		DATA_TYPE = 
		case 
			when d.data_type = 11
				then convert(smallint,93)
		else
			d.data_type+convert(smallint,
					  isnull(d.aux,
					     ascii(substring("666AAA@@@CB??GG",
						          2*(d.ss_dtype%35+1)
							  +2-8/d.length,1))
						          -60))
		end,
		TYPE_NAME = d.type_name,
		COLUMN_SIZE = isnull(d.data_precision, convert(int,d.length))
			     +isnull(d.aux, convert(int,
					     ascii(substring("???AAAFFFCKFOLS",
						          2*(d.ss_dtype%35+1)
							  +2-8/d.length,1))
							  -60)),
		BUFFER_LENGTH = isnull(d.length, convert(int,t.length))
			 +convert(int, isnull(d.aux,
					     ascii(substring("AAA<BB<DDDHJSPP",
						    	     2*(d.ss_dtype%35
							     +1)+2-8/t.length,
						             1))-64)),
		DECIMAL_DIGITS = d.numeric_scale +convert(smallint,
					   isnull(d.aux,
					     ascii(substring("<<<<<<<<<<<<<<?",
						        2*(d.ss_dtype%35+1)
							+2-8/d.length,
						        1))-60)),
		NUM_PREC_RADIX = d.numeric_radix,
		NULLABLE = convert(smallint, 1),
		REMARKS = convert(varchar(254),NULL),	/* Remarks are NULL */
                COLUMN_DEF = convert(varchar(254),NULL),
                SQL_DATA_TYPE = isnull(d.sql_data_type,
			d.data_type+convert(smallint,
                	isnull(d.aux,
                        ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/d.length,1))
                        -60))),
                SQL_DATETIME_SUB = NULL,
                CHAR_OCTET_LENGTH = NULL,
                ORDINAL_POSITION = convert(tinyint, 0),
                IS_NULLABLE = 'YES'
	from
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t
	where
		o.id = @procedure_id
		and d.ss_dtype = 56  /* int for return code */
		and t.type = 56
		and o.type = 'P'
		and (@column_name = '%' or @column_name = 'RETURN_VALUE')
	union
	select		   /* All other types including user data types */
		PROCEDURE_CAT = db_name(),
		PROCEDURE_SCHEM = user_name(o.uid),
		PROCEDURE_NAME = o.name,
		COLUMN_NAME = 	
			case	
		 	    when c.name = 'Return Type' then 'RETURN_VALUE'
			    else c.name
			end,
		COLUMN_TYPE = 
		case 
			when c.name = 'Return Type' 
				then convert(smallint, 5)
--		when c.status2 = 1
--			then convert(smallint, 1)
--		when c.status2 = 2
--			then convert(smallint, 4)
--		when c.status2 = 4			     		
--			then  convert(smallint, 2)
		else convert(smallint, 0)	
		end,		

		/*   Map systypes.type to ODBC type	       		*/
		/*   SS-Type "				 1	      "	*/
		/*	     "33 3 3 4 44 5 5 2 5 55666"	        */
		/*	     "45 7 9	5 78 0 2 2 6 89012"             */
		DATA_TYPE = 
		case 
			when t.name = "date"
				then convert(smallint,91)
			when t.name = "time"
				then convert(smallint,92)
			when t.name = "datetime"
				then convert(smallint,93)
		else
			d.data_type+convert(smallint,
			isnull(d.aux, ascii(substring("666AAA@@@CB??GG",
			2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60))
		end,
		TYPE_NAME = 
			case 
			    when t.name = 'extended type' 
				then isnull(get_xtypename(c.xtype, c.xdbid), 
									t.name)
			    when t.type = 58
			    	then "smalldatetime"
			    when t.usertype in (44,45,46)
				then "unsigned "+substring(t.name,
				charindex("u",t.name) + 1,
				charindex("t",t.name))
			    else 
				t.name
			end,
		COLUMN_SIZE = 
		case 
			when d.data_precision = 0
			then convert(int,0)
		else		
		isnull(convert(int, c.prec),
			isnull(d.data_precision, convert(int,c.length)))
			     +isnull(d.aux, convert(int,
					     ascii(substring("???AAAFFFCKFOLS",
						       2*(d.ss_dtype%35+1)
						       +2-8/c.length,1))
						       -60))
		end,
		BUFFER_LENGTH = isnull(d.length, convert(int,c.length))
			 +convert(int, isnull(d.aux,
					     ascii(substring("AAA<BB<DDDHJSPP",
						             2*(d.ss_dtype%35
							     +1)+2-8/c.length,
						             1))-64)),
		DECIMAL_DIGITS = isnull(convert(smallint, c.scale),
			convert(smallint, d.numeric_scale))
			+ convert(smallint,
					  isnull(d.aux,
					    ascii(substring("<<<<<<<<<<<<<<?",
							    2*(d.ss_dtype%35+1)
							    +2-8/c.length,
							    1))-60)),
		NUM_PREC_RADIX = d.numeric_radix,

		/* set nullability from status flag */
		NULLABLE = convert(smallint,1),/*convert(smallint, convert(bit, c.status&8)),*/
		REMARKS = convert(varchar(254),NULL),	/* Remarks are NULL */
                COLUMN_DEF = convert(varchar(254),NULL),
                SQL_DATA_TYPE = isnull(d.sql_data_type,
			d.data_type+convert(smallint,
                	isnull(d.aux,
                        ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/c.length,1))
                        -60))),
                SQL_DATETIME_SUB = 
		case
			when (isnull(d.sql_data_type,d.data_type+convert(smallint,
				isnull(d.aux,ascii(substring("666AAA@@@CB??GG",
				2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60)))) = 91
				then convert(smallint,1)
			when (isnull(d.sql_data_type,d.data_type+convert(smallint,
				isnull(d.aux,ascii(substring("666AAA@@@CB??GG",
				2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60)))) = 92
				then convert(smallint,2)
			when (isnull(d.sql_data_type,d.data_type+convert(smallint,
	                	isnull(d.aux,ascii(substring("666AAA@@@CB??GG",
	                        2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60)))) = 93
		                then convert(smallint,3)
                	end,
		CHAR_OCTET_LENGTH = 
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision
		** if not, return a 0 and multiply it by the precision
		*/
		case 
			when d.data_type = 4 then convert(smallint,NULL)
		else
			convert(smallint,
		    	substring('0111111',
			charindex(char(c.type),
			@char_bin_types)+1, 1)) *
			/* calculate the precision */
			isnull(convert(int, c.prec),
		    	isnull(convert(int, d.data_precision),
			convert(int, c.length)))
		   	+isnull(d.aux, convert(int,
			ascii(substring('???AAAFFFCKFOLS',
			   2*(d.ss_dtype%35+1)+2-8/c.length,1))-60))
                end,
		ORDINAL_POSITION = convert(int,c.colid),
		IS_NULLABLE = 'YES'/*rtrim(substring('NO YES',
                        (convert(smallint, convert(bit, c.status&8))*3)+1, 3))*/
	from
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t
	where
		o.id = @procedure_id
		and c.id = o.id
		and c.type *= d.ss_dtype
		and c.usertype *= t.usertype
		and c.name like @column_name
		and c.number = @group_num
		and d.ss_dtype not in (111, 109, 38, 110) /* No *N types */

	 order by convert(int,colid)
end
else
begin
	/* 
	** this block is for the case where there IS pattern
	** matching done on the table name
	*/
	if @procedure_owner is null
		select @procedure_owner = '%'

	select	/* INTn, FLOATn, DATETIMEn and MONEYn types */
		PROCEDURE_CAT = db_name(),
		PROCEDURE_SCHEM = user_name(o.uid),
		PROCEDURE_NAME = o.name,
                COLUMN_NAME =
                        case
                            when c.name = 'Return Type' then 'RETURN_VALUE'
                            else c.name
                        end,
                COLUMN_TYPE =
		case
			when c.name = 'Return Type'
                             	then convert(smallint, 5)
--		when c.status2 = 1
--			then convert(smallint, 1)
--		when c.status2 = 2
--			then convert(smallint, 4)
--		when c.status2 = 4			     		
--			then  convert(smallint, 2)
                  else convert(smallint, 0)
		end,
		DATA_TYPE = 
		case 
			when d.data_type = 11
				then convert(smallint,93)
		else
			d.data_type+convert(smallint,
					  isnull(d.aux,
					     ascii(substring("666AAA@@@CB??GG",
						          2*(d.ss_dtype%35+1)
							  +2-8/c.length,1))
						          -60))
		end,
		TYPE_NAME = rtrim(substring(d.type_name,
				    1+isnull(d.aux,
					     ascii(substring("III<<<MMMI<<A<A",
					                  2*(d.ss_dtype%35+1)
							  +2-8/c.length,
						          1))-60), 18)),
		COLUMN_SIZE = isnull(convert(int, c.prec), 
				isnull(d.data_precision, convert(int,c.length)))
			     +isnull(d.aux, convert(int,
					     ascii(substring("???AAAFFFCKFOLS",
						           2*(d.ss_dtype%35+1)
							   +2-8/c.length,1))
						           -60)),
		BUFFER_LENGTH = isnull(d.length, convert(int,c.length))
			 +convert(int, isnull(d.aux,
					     ascii(substring("AAA<BB<DDDHJSPP",
							   2*(d.ss_dtype%35+1)
							   +2-8/c.length,
							   1))-64)),
		DECIMAL_DIGITS = isnull(convert(smallint, c.scale),
				convert(smallint, d.numeric_scale))
				+ convert(smallint,
					    isnull(d.aux,
					     ascii(substring("<<<<<<<<<<<<<<?",
							   2*(d.ss_dtype%35+1)
							   +2-8/c.length,
							   1))-60)),
		NUM_PREC_RADIX = d.numeric_radix,
		/* set nullability from status flag */
		NULLABLE = convert(smallint,1), /*convert(smallint, convert(bit, c.status&8)),*/
		REMARKS = convert(varchar(254),NULL),	/* Remarks are NULL */
                COLUMN_DEF = convert(varchar(254),NULL),
                SQL_DATA_TYPE = isnull(d.sql_data_type,
			d.data_type+convert(smallint,
                	isnull(d.aux,
                        ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/c.length,1))
                        -60))),
                SQL_DATETIME_SUB = NULL,
		CHAR_OCTET_LENGTH = 
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision
		** if not, return a 0 and multiply it by the precision
		*/
		case 
			when d.data_type = 4 then convert(smallint,NULL)
		else
			convert(smallint,
		    	substring('0111111',
			charindex(char(c.type),
			@char_bin_types)+1, 1)) *
			/* calculate the precision */
			isnull(convert(int, c.prec),
		    	isnull(convert(int, d.data_precision),
			convert(int, c.length)))
		    	+isnull(d.aux, convert(int,
			ascii(substring('???AAAFFFCKFOLS',
			   2*(d.ss_dtype%35+1)+2-8/c.length,1))-60))
		end,
                ORDINAL_POSITION = convert(int,c.colid),
                IS_NULLABLE = 'YES' /* rtrim(substring('NO YES',
                        (convert(smallint, convert(bit, c.status&8))*3)+1, 3))*/
	from
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t
	where
		o.name like @procedure_name
		and user_name(o.uid) like @procedure_owner
		and o.id = c.id
		and c.type = d.ss_dtype
		and c.name like @column_name
		
		/* Just procs & sqlj procs and funcs */
		and o.type in ('P', 'F')
		and d.ss_dtype in (111, 109, 38, 110)	/* Just *N types */
	union
	select distinct
		PROCEDURE_CAT = db_name(),
		PROCEDURE_SCHEM = user_name(o.uid),
		PROCEDURE_NAME = o.name ,
		COLUMN_NAME = 'RETURN_VALUE',
		COLUMN_TYPE = convert(smallint, 5), /* return parameter */
		DATA_TYPE = 
		case 
			when d.data_type = 11
			then convert(smallint,93)
		else
			d.data_type+convert(smallint,
					  isnull(d.aux,
					     ascii(substring("666AAA@@@CB??GG",
						          2*(d.ss_dtype%35+1)
							  +2-8/d.length,1))
						          -60))
		end,
		TYPE_NAME = d.type_name,
		COLUMN_SIZE = isnull(d.data_precision, convert(int,d.length))
			     +isnull(d.aux, convert(int,
					     ascii(substring("???AAAFFFCKFOLS",
						          2*(d.ss_dtype%35+1)
							  +2-8/d.length,1))
							  -60)),
		BUFFER_LENGTH = isnull(d.length, convert(int,t.length))
			 +convert(int, isnull(d.aux,
					     ascii(substring("AAA<BB<DDDHJSPP",
						    	     2*(d.ss_dtype%35
							     +1)+2-8/t.length,
						             1))-64)),
		DECIMAL_DIGITS = d.numeric_scale +convert(smallint,
					   isnull(d.aux,
					     ascii(substring("<<<<<<<<<<<<<<?",
						        2*(d.ss_dtype%35+1)
							+2-8/d.length,
						        1))-60)),
		NUM_PREC_RADIX = d.numeric_radix,
		NULLABLE = convert(smallint, 1),
		REMARKS = convert(varchar(254),NULL),	/* Remarks are NULL */
                COLUMN_DEF = convert(varchar(254),NULL),
                SQL_DATA_TYPE = isnull(d.sql_data_type,
			d.data_type+convert(smallint,
                	isnull(d.aux,
                        ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/d.length,1))
                        -60))),
                SQL_DATETIME_SUB = NULL,
                CHAR_OCTET_LENGTH = NULL,
                ORDINAL_POSITION = convert(tinyint, 0),
                IS_NULLABLE = 'YES'
	from
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t,
		sysprocedures p
	where
		o.name like @procedure_name
		and user_name(o.uid) like @procedure_owner
		and d.ss_dtype = 56  /* int for return code */
		and t.type = 56
		and o.type = 'P'			/* Just Procedures */
		and p.id = o.id
		and 'RETURN_VALUE' like @column_name
	union
	select		   /* All other types including user data types */
		PROCEDURE_CAT = db_name(),
		PROCEDURE_SCHEM = user_name(o.uid),
		PROCEDURE_NAME = o.name,
                COLUMN_NAME =
		case
			when c.name = 'Return Type' then 'RETURN_VALUE'
			else c.name
		end,
                COLUMN_TYPE =
		case
			when c.name = 'Return Type'
				then convert(smallint, 5)
--		when c.status2 = 1
--			then convert(smallint, 1)
--		when c.status2 = 2
--			then convert(smallint, 4)
--		when c.status2 = 4			     		
--			then  convert(smallint, 2)                                        
			else convert(smallint, 0)
		end,
		/*   Map systypes.type to ODBC type    			*/
		/*   SS-Type  "				 1	      " */
		/*	      "33 3 3 4 44 5 5 2 5 55666"		*/
		/*	      "45 7 9 5 78 0 2 2 6 89012"    		*/
		DATA_TYPE = 
		case 
			when t.name = "date"
			then convert(smallint,91)
			when t.name = "time"
			then convert(smallint,92)
			when t.name = "datetime"
			then convert(smallint,93)
			
		   else		
			d.data_type+convert(smallint,
					  isnull(d.aux,
					     ascii(substring("666AAA@@@CB??GG",
						          2*(d.ss_dtype%35+1)
							  +2-8/c.length,1))
						          -60))
		end,
		TYPE_NAME =
                        case 
                            when t.name = 'extended type' 
                                then isnull(get_xtypename(c.xtype, c.xdbid),
									t.name)
			    when t.type = 58
			    	then "smalldatetime"
			    when t.usertype in (44,45,46)
				then "unsigned "+substring(t.name,
				charindex("u",t.name) + 1,
				charindex("t",t.name))
                            else 
                                t.name
                        end,


		COLUMN_SIZE = 
		case 
			when d.data_precision = 0
			then convert(int,0)
		else
		isnull(convert(int, c.prec),
			isnull(d.data_precision, convert(int,c.length)))
			     +isnull(d.aux, 
				     convert(int,
					     ascii(substring("???AAAFFFCKFOLS",
					                   2*(d.ss_dtype%35+1)
							   +2-8/c.length,1))
					           -60))
		end,
		BUFFER_LENGTH = isnull(d.length, convert(int,c.length))
			 +convert(int,
				  isnull(d.aux,
					 ascii(substring("AAA<BB<DDDHJSPP",
					                 2*(d.ss_dtype%35+1)
							 +2-8/c.length,
					                 1))-64)),
		DECIMAL_DIGITS = isnull(convert(smallint, c.scale),
			convert(smallint, d.numeric_scale))
			+ convert(smallint,
				 isnull(d.aux,
					ascii(substring("<<<<<<<<<<<<<<?",
					                2*(d.ss_dtype%35+1)
							+2-8/c.length,
					                1))-60)),
		NUM_PREC_RADIX = d.numeric_radix,
		/* set nullability from status flag */
		NULLABLE = convert(smallint,1), /*convert(smallint, convert(bit, c.status&8)),*/
		REMARKS = convert(varchar(254),NULL),	/* Remarks are NULL */
                COLUMN_DEF = convert(varchar(254),NULL),
                SQL_DATA_TYPE = isnull(d.sql_data_type,
			d.data_type+convert(smallint,
                	isnull(d.aux,
                        ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/c.length,1))
                        -60))),
                SQL_DATETIME_SUB = 
                case
                	when (isnull(d.sql_data_type,d.data_type+convert(smallint,
                	isnull(d.aux,ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60)))) = 91
                        then convert(smallint,1)
                	when (isnull(d.sql_data_type,d.data_type+convert(smallint,
                	isnull(d.aux,ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60)))) = 92
                        then convert(smallint,2)
                	when (isnull(d.sql_data_type,d.data_type+convert(smallint,
                	isnull(d.aux,ascii(substring("666AAA@@@CB??GG",
                        2*(d.ss_dtype%35+1)+2-8/c.length,1)) -60)))) = 93
                        then convert(smallint,3)
                end,
		CHAR_OCTET_LENGTH = 
		/*
		** check if in the list
		** if so, return a 1 and multiply it by the precision
		** if not, return a 0 and multiply it by the precision
		*/
		case 
			when d.data_type = 4 then convert(smallint,NULL)
		else
			convert(smallint,
		    	substring('0111111',
			charindex(char(c.type),
			@char_bin_types)+1, 1)) *
			/* calculate the precision */
			isnull(convert(int, c.prec),
		    	isnull(convert(int, d.data_precision),
			convert(int, c.length)))
		    	+isnull(d.aux, convert(int,
			ascii(substring('???AAAFFFCKFOLS',
			   2*(d.ss_dtype%35+1)+2-8/c.length,1))-60))
		end,
                ORDINAL_POSITION = convert(int,c.colid),
                IS_NULLABLE = 'YES' /*rtrim(substring('NO YES',
                        (convert(smallint, convert(bit, c.status&8))*3)+1, 3))*/
	from
		syscolumns c,
		sysobjects o,
		sybsystemprocs.dbo.spt_datatype_info d,
		systypes t
	where
		o.name like @procedure_name
		and user_name(o.uid) like @procedure_owner
		and o.id = c.id
		and c.type *= d.ss_dtype
		and c.usertype *= t.usertype

                /* Just procs & sqlj procs and funcs */
		and o.type in ('P', 'F')
		and c.name like @column_name
		and d.ss_dtype not in (111, 109, 38, 110) /* No *N types */

	order by PROCEDURE_SCHEM, PROCEDURE_NAME, convert(int,colid)
end


go
exec sp_procxmode 'sp_odbc_getprocedurecolumns', 'anymode'
go
grant execute on sp_odbc_getprocedurecolumns to public
go
dump tran master with truncate_only
go
dump transaction sybsystemprocs with truncate_only
go


print ""
go
print "Installed odbc_mda Stored Procedures ..."
go
declare @retval int
declare @version_string varchar(255) 
select @version_string = '15.7.0.80.1008/'+ 'Fri Aug 26 UTC 01:00:28 2011'
exec @retval = sp_version 'ODBC MDA Scripts', NULL, @version_string, 'end'
if (@retval != 0) select syb_quit()
go
