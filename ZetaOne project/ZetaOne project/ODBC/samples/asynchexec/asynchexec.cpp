/*
Copyright (c) 2003-2006  Sybase, Inc.

Module Name:
	asynchexec.cpp

Abstract:
 	Sample ODBC console application.
 	Executes statement asynchronously

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
#ifdef  LINUX
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


void executeStatement(SQLHSTMT, SQLTCHAR*);
void finish(SQLHENV , SQLHDBC , SQLHSTMT, bool);
void sqlok(SQLHSTMT stmt, SQLRETURN retcode, char* message);
template <typename T>
bool cmp(T* str1, char* str2);
using namespace std;

#define AU_ID_LEN 12
#define STMT_LEN 255
#define AU_FNAME_LEN 21
#define ERR_MSG_LEN	255
/**
 * The mode for 'asynchronous execution' is 'per-statement' by default,
 * if you wish to run application in 'per-connection' level 'asynchronous execution',
 * simply supply the command line argument 'conn' when you start the application.
 *
 * In order to run this application successfully, you need to first create ODBC
 * DSN 'sampledsn'.
 */

#if defined(WIN32) && defined(UNICODE)
int wmain(int argc, wchar_t* argv[])
#else
int main(int argc, char* argv[])
#endif
{
	SQLHENV		env	= SQL_NULL_HANDLE;
	SQLHDBC		dbc	= SQL_NULL_HANDLE;
	SQLHDBC		dbcAsync	= SQL_NULL_HANDLE;
	SQLHSTMT 	stmt = SQL_NULL_HANDLE;
	SQLHSTMT 	stmtAsync = SQL_NULL_HANDLE;
	SQLRETURN 	retcode;
	SQLRETURN 	retcodeA;
	SQLTCHAR	connString[512];
	SQLLEN 		aufNameLen = 0;
	SQLCHAR		aufName[ AU_FNAME_LEN ];
	SQLLEN 		versionLen = 0;
	SQLCHAR		versionString[ STMT_LEN ];
	SQLTCHAR*	 selectstmt = _ODBCSTRTYPE("select au_fname from authors");
	SQLTCHAR*	dropSP = _ODBCSTRTYPE("drop proc waitexec");
	SQLTCHAR*	createSP = _ODBCSTRTYPE("Create proc waitexec as waitfor delay \"00:00:05\" select @@version");
	SQLTCHAR*	execSP = _ODBCSTRTYPE("exec waitexec");
	int lengthOfDefault = strlen("DSN=sampledsn");
	bool usePerStmt = true;

	//Process command line argument if any.
	if (argc > 1 && cmp(argv[1], "conn"))
	{
		usePerStmt = false;
		cout << "Running 'per-connection' level asynchronous execution. " << endl;
	}
	else
	{
		cout << "Running 'per-statement' level asynchronous execution. " << endl;
	}

	//Allocate Environment Handle.
	retcode = SQLAllocHandle(SQL_HANDLE_ENV, SQL_NULL_HANDLE, &env);

	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO)
	{
		cout << "Failed to allocate Environment Handle, terminating application; SQLRETURN code is :" << retcode ;
		exit(1);
	}

	/* Set the ODBC version environment attribute */
	retcode = SQLSetEnvAttr(env, SQL_ATTR_ODBC_VERSION, (void*)SQL_OV_ODBC3, 0);
	/* Allocate connection handle */
	retcode = SQLAllocHandle(SQL_HANDLE_DBC, env, &dbc);
	sqlok(stmt, retcode, (char *)"Allocating connection Handle failed");

	/* Allocate asynchronous connection handle */
	retcode = SQLAllocHandle(SQL_HANDLE_DBC, env, &dbcAsync);
	sqlok(stmt, retcode, (char *)"Allocating connection handle failed");

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
	retcode = SQLDriverConnect(dbcAsync, SQL_NULL_HANDLE, connString, SQL_NTS, SQL_NULL_HANDLE, 0, SQL_NULL_HANDLE, SQL_DRIVER_NOPROMPT);
	sqlok(stmt, retcode, (char *)"Obtaining a connection failed");

	retcode = SQLAllocHandle(SQL_HANDLE_STMT, dbc, &stmt);
	sqlok(stmt, retcode, (char *)"Allocating statement handle failed");
	retcode = SQLAllocHandle(SQL_HANDLE_STMT, dbcAsync, &stmtAsync);
	sqlok(stmt, retcode, (char *)"Allocating statement handle failed");
	executeStatement(stmt, createSP);

	/**
	 The following demonstrates use of both 'asynchronous execution' modes.
	 */
	if (usePerStmt == true)
	{
		//Set attribute to enable per-statement level asynch
		retcode = SQLSetStmtAttr(stmtAsync, SQL_ATTR_ASYNC_ENABLE, (SQLPOINTER)SQL_ASYNC_ENABLE_ON, 0);
		cout << "Enabled 'per-statement' asynchronous call for stmtAsync. " << endl;
	}
	else
	{
		//Set attribute to enable connection level asynch
		retcode = SQLSetConnectAttr(dbcAsync, SQL_ATTR_ASYNC_ENABLE, (SQLPOINTER)SQL_ASYNC_ENABLE_ON, 0);
		cout << "Enabled 'per-connection' asynchronous call for dbcAsync. " << endl;
	}

	int i = 0;

	while ((retcodeA = SQLExecDirect(stmtAsync, execSP, SQL_NTS)) == SQL_STILL_EXECUTING) //StmtAsync now is running asynchronously
	{
		//Perform additional tasks while executing stored procedure 'execSP'.
		executeStatement(stmt, selectstmt) ;
		retcode = SQLBindCol(stmt, 1, SQL_C_CHAR, aufName, sizeof(aufName), &aufNameLen);
		retcode = SQLFetch(stmt);
		retcode = SQLFreeStmt(stmt, SQL_CLOSE);
		i ++;
	}

	cout << "Application polled " << i << " times while in Async mode. " << endl;
	sqlok(stmtAsync, retcodeA, (char *)"Asynchronously executing statement failed");

	//Bind column and fetch results.
	retcode = SQLBindCol(stmtAsync, 1, SQL_C_CHAR, versionString, sizeof(versionString), &versionLen);

	while (retcodeA == SQL_SUCCESS || retcodeA == SQL_SUCCESS_WITH_INFO)
	{
		while ((retcodeA = SQLFetch(stmtAsync)) == SQL_STILL_EXECUTING)
		{
		}
		sqlok(stmtAsync, retcodeA, (char *)"Fetch result set failed");

		if (retcodeA != SQL_NO_DATA)
		{
			cout << "Current server version is : " << versionString << endl;
		}
	}//end while

	//Done, clean-up and terminate application.
	cout << " End of Sample " << endl;
	executeStatement(stmt, dropSP);
	finish(NULL, dbcAsync, stmtAsync, false);
	finish(env, dbc, stmt, false);
	return 0;
}

/**
**	executeStatement
**
**	Executes a sql statement
**/
void executeStatement(SQLHSTMT stmt, SQLTCHAR* statement)
{
	SQLRETURN retcode;
	SQLTCHAR 	errormsg[ERR_MSG_LEN];
	SQLTCHAR	sqlstate[SQL_SQLSTATE_SIZE+1];
	SQLINTEGER	nativeerror = 0;
	SQLSMALLINT errormsglen = 0;
	retcode = SQLExecDirect(stmt, statement, SQL_NTS) ;

	if (retcode != SQL_SUCCESS && retcode != SQL_SUCCESS_WITH_INFO)
	{
		cout << "Executing Statement : ";
		TCOUT << statement;
		cout << " failed SQLRETURN code is " << retcode  << endl;

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
	}
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

template <typename T>
bool cmp(T* str1, char* str2)
{
	do
	{
		if(*str1 != *str2)
		{
			return false;
		}
		str1++;
		str2++;
	}while((*str1 !=0) && (*str2 != 0));
	return (*str1 == *str2);
}
