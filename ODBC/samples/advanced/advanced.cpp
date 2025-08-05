/*
Copyright (c) 2003-2006  Sybase, Inc.

Module Name:
	advanced.cpp

Abstract:
 	Sample ODBC console application.
 	Uses stored procedures to perform database operations

*/


#if defined (WIN32) || defined(_WIN32)
#include <windows.h>
#else
#include <stdlib.h>
#include <stddef.h>
#endif
#include <string.h>
#include <sql.h>
#include <sqlext.h>
#include <iostream>
#ifdef	LINUX
#ifndef SQLLEN
#define SQLLEN SQLINTEGER
#endif
#ifndef SQLULEN
#define SQLULEN SQLUINTEGER
#endif
#endif
#ifndef _ODBCSTRTYPE
#if defined(UNICODE) || defined(_UNICODE)
#define _ODBCSTRTYPE(str)		(SQLWCHAR *)L##str
#else
#define _ODBCSTRTYPE(str)		(SQLCHAR *)str
#endif
#endif
#ifndef TCOUT
#if defined(UNICODE) || defined(_UNICODE)
#define TCOUT		wcout
#else
#define TCOUT		cout
#endif
#endif
#ifndef TCIN
#if defined(UNICODE) || defined(_UNICODE)
#define TCIN(str,len)		wcin.getline((wchar_t*)str, len)
#else
#define TCIN(str,len)		cin.getline((char*)str, len)
#endif
#endif

void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit);
void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message);
using namespace std;

#define STOR_ID_LEN 4
#define ORD_NUM_LEN 20
#define STMT_LEN 155
#define PROC_LEN 255
#define ERR_MSG_LEN	255
#define DATE_LEN 40

#if defined(WIN32) && defined(UNICODE)
int wmain(int argc, wchar_t* argv[])
#else
int main(int argc, char* argv[])
#endif
{
	SQLHENV	env	 = SQL_NULL_HANDLE;
	SQLHDBC	dbc	= SQL_NULL_HANDLE;
	SQLHSTMT 	stmt = SQL_NULL_HANDLE;
	SQLRETURN 	retcode;
	SQLTCHAR	connString[512];
	SQLTCHAR*	 createproc1 = _ODBCSTRTYPE("create procedure sp_selectsales (@stor_id char(4),@ordnum varchar(20) output, @date varchar(40)) as begin select  @ordnum = ord_num  from sales where stor_id = @stor_id and date = @date  return @@rowcount end");
	SQLTCHAR*	 callproc1 = _ODBCSTRTYPE("{ ?  = call sp_selectsales(?,?,?) }");
	SQLTCHAR*	 dropproc1 = _ODBCSTRTYPE("if exists (select 1 from sysobjects where name = 'sp_selectsales' and type = 'P') drop procedure sp_selectsales");
	SQLTCHAR*	 createproc2 = _ODBCSTRTYPE("create procedure sp_multipleresults (@stor_id char(4) ) as begin select ord_num from sales where stor_id = @stor_id  select date from sales where @stor_id = stor_id end");
	SQLTCHAR*	 callproc2 = _ODBCSTRTYPE("{ call sp_multipleresults(?) }");
	SQLTCHAR*	 dropproc2 = _ODBCSTRTYPE("if exists (select 1 from sysobjects where name = 'sp_multipleresults' and type = 'P') drop procedure sp_multipleresults");
	SQLCHAR stor_id[STOR_ID_LEN+1] = "5023";
	SQLCHAR ord_num[ORD_NUM_LEN+1];
	SQLCHAR date[DATE_LEN+1] = "Oct 31 1985 12:00AM";
	SQLLEN ordnumLen = 0, dateLen = SQL_NTS, dbValueLen = 0;
	SQLCHAR dbValue[DATE_LEN+1];
	int lengthOfDefault = strlen("DSN=sampledsn");
	retcode = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env);

	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO)
	{
		cout << "Allocating Environment Handle failed; SQLRETURN code is :" << retcode ;
		exit(1);
	}

	/* Set the ODBC version environment attribute */
	retcode = SQLSetEnvAttr(env, SQL_ATTR_ODBC_VERSION, (void*)SQL_OV_ODBC3, 0);

	retcode = SQLAllocHandle(SQL_HANDLE_DBC, env, &dbc);
	sqlok(stmt, retcode, (char *)"Allocating connection Handle failed");

	if(argc == 4)
	{
#if defined(UNICODE)
#if defined(WIN32)
		wstring tmpConnString = wstring(L"DSN=");
		tmpConnString += wstring(argv[1]);
		tmpConnString += wstring(L";UID=");
		tmpConnString += wstring(argv[2]);
		tmpConnString += wstring(L";PWD=");
		tmpConnString += wstring(argv[3]);
		wcout << L"Using connection string \"" << tmpConnString.c_str() << L"\"" << endl;
		memcpy(connString, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length()] = 0;
#else
		//The connection string is hard coded because wmain is non-standared c++
		//A complete string converter, which is not in the scope of this sample, would be required for command line input
		//NOTE we are only able to build with UNICODE defined on platforms that allow the
		//redefinition of wchar_t from 32bit to 16bit to match SQLWCHAR
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault] = 0;
#endif
#else
		string tmpConnString = string("DSN=");
		tmpConnString += string(argv[1]);
		tmpConnString += string(";UID=");
		tmpConnString += string(argv[2]);
		tmpConnString += string(";PWD=");
		tmpConnString += string(argv[3]);
		cout << "Using connection string \"" << tmpConnString.c_str() << "\"" << endl;
		memcpy(connString, tmpConnString.c_str(), tmpConnString.length()*sizeof(SQLTCHAR));
		connString[tmpConnString.length()] = 0;
#endif
	}
	else
	{
		cout << "Using connection string \"DSN=sampledsn\"" << endl;
		memcpy(connString, _ODBCSTRTYPE("DSN=sampledsn"), lengthOfDefault*sizeof(SQLTCHAR));
		connString[lengthOfDefault] = 0;
	}
	retcode = SQLDriverConnect(dbc, SQL_NULL_HANDLE, connString, SQL_NTS, SQL_NULL_HANDLE, 0, SQL_NULL_HANDLE, SQL_DRIVER_NOPROMPT);
	sqlok(stmt, retcode, (char *)"Obtaining a connection failed");

	retcode = SQLAllocHandle(SQL_HANDLE_STMT, dbc, &stmt);
	sqlok(stmt, retcode, (char *)"Allocating statement handle failed");
	retcode = SQLExecDirect(stmt, dropproc1, SQL_NTS) ;
	cout << "** STORED PROCEDURE PARAMETER SAMPLE **" << endl ;
	retcode = SQLExecDirect(stmt, createproc1, SQL_NTS) ;
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	cout <<  "created stored procedure  successfully " << endl;
	SQLINTEGER retVal = 0;
	retcode = SQLBindParameter(stmt, 1, SQL_PARAM_OUTPUT, SQL_C_SLONG, SQL_INTEGER , 0, 0, &retVal, 0 , SQL_NULL_HANDLE);
	retcode = SQLBindParameter(stmt, 2, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR , 4, 0, stor_id, sizeof(stor_id) , SQL_NULL_HANDLE);
	retcode = SQLBindParameter(stmt, 3, SQL_PARAM_OUTPUT, SQL_C_CHAR, SQL_VARCHAR , 20, 0, ord_num, sizeof(ord_num) , &ordnumLen);
	retcode = SQLBindParameter(stmt, 4, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_VARCHAR , 40, 0, date, sizeof(date) , &dateLen);
	retcode = SQLExecDirect(stmt, callproc1, SQL_NTS) ;
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	cout <<  "executed stored procedure successfully " << endl;
	cout << "   The ORDER NUMBER is : " << ord_num << endl;
	cout << "   The RETURN VALUE from the procedure is : " << retVal << endl;
	//Close any result sets and cursors
	retcode = SQLFreeStmt(stmt, SQL_CLOSE);
	//Free the bound parameters
	retcode = SQLFreeStmt(stmt, SQL_RESET_PARAMS);
	retcode = SQLExecDirect(stmt, dropproc1, SQL_NTS);
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	//multiple results
	retcode = SQLExecDirect(stmt, dropproc2, SQL_NTS);
	cout << " \n *** MULTIPLE RESULTS SAMPLE ***" << endl;
	retcode = SQLExecDirect(stmt, createproc2, SQL_NTS);
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	retcode = SQLBindParameter(stmt, 1, SQL_PARAM_INPUT, SQL_C_CHAR, SQL_CHAR , 4, 0, stor_id, sizeof(stor_id) , SQL_NULL_HANDLE);
	retcode = SQLExecDirect(stmt, callproc2, SQL_NTS);
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	retcode = SQLBindCol(stmt, 1, SQL_C_CHAR, dbValue, sizeof(dbValue), &dbValueLen);
	cout << "-- Iterating the resultset --"  << endl;
	SQLSMALLINT count = 1;

	while (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
	{
		retcode = SQLFetch(stmt);

		sqlok(stmt, retcode, (char *)"SQLFetch failed");

		if (retcode == SQL_NO_DATA)
		{
			cout << "\n -- End of result set --  " << count << endl;

			if (count == 1)
			{
				retcode = SQLMoreResults(stmt);
				count ++;
			}
		}
		else
		{
			if (count == 1)
			{
				cout << " ORDER NUMBER : " << dbValue;
			}
			else
			{
				cout << " DATE : " << dbValue;
			}
		}
	}//end while

	SQLFreeStmt(stmt, SQL_CLOSE); //close the result set
	retcode = SQLExecDirect(stmt, dropproc2, SQL_NTS) ;
	sqlok(stmt, retcode, (char *)"SQLExecDirect failed");

	cout <<  "dropped stored procedure successfully " << endl;
	finish(env, dbc, stmt, false);
	return 0;
}



void finish(SQLHENV env, SQLHDBC dbc, SQLHSTMT stmt, bool doExit)
{
	if (stmt != SQL_NULL_HANDLE)
	{
		SQLFreeStmt(stmt, SQL_CLOSE); //close the result set
		SQLFreeHandle(SQL_HANDLE_STMT, stmt);
	}

	if (dbc != SQL_NULL_HANDLE)
	{
		SQLDisconnect(dbc);
		SQLFreeHandle(SQL_HANDLE_DBC, dbc);
	}

	if (env != SQL_NULL_HANDLE)
	{
		SQLFreeHandle(SQL_HANDLE_ENV, env);
	}

	if (doExit)
	{
		exit(1);
	}
}

void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message)
{
	SQLTCHAR errormsg[ERR_MSG_LEN], sqlstate[SQL_SQLSTATE_SIZE+1];
	SQLINTEGER nativeerror = 0;
	SQLSMALLINT errormsglen = 0;
	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO && retcode != SQL_NO_DATA)
	{
		cout << message << endl;
		cout << "SQLRETURN code is " << retcode ;
		if (retcode == SQL_ERROR)
		{
			retcode = SQLGetDiagRec(SQL_HANDLE_STMT, stmt, 1, sqlstate, &nativeerror, errormsg, ERR_MSG_LEN, &errormsglen);

			if (retcode == SQL_SUCCESS || retcode == SQL_SUCCESS_WITH_INFO)
			{
				cout << " SqlState : ";
				TCOUT << sqlstate;
				cout << " Error Message :";
				TCOUT << errormsg;
				cout << endl ;
			}
		}
		exit(1);
	}
}
