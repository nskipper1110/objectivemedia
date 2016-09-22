/*
 * copyright (c) 2013 Nathan Skipper, Montgomery Technology, Inc.
 *
 * This file is part of ObjectiveMedia (http://nskipper1110.github.com/objectivemedia).
 *
 * ObjectiveMedia is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * ObjectiveMedia is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with ObjectiveMedia; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
 */
package com.mti.primitives;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.util.Vector;
import java.io.BufferedInputStream;
/**
 *
 * @author nathan
 */
public abstract class Primitives {
    
    final static String Version = "1.0.1";
    /**
     * The LibraryPath global variable should define the file folder location
     * for the JNI enabled dynamic library that implements the functions needed
     * for this class library. This value must be set before any class within this
     * namespace can be declared or instantiated.
     */
    public static String LibraryPath = "";
    /**
     * The DependencyPaths list should define any dependencies that are used
     * by this library and/or it's JNI library. The values provided to this vector
     * can either be a file path or a HTTP URL. When the "InitializePrimitives"
     * function is called, the function will download or copy all dependencies
     * defined in this list to the path specified by "LibraryPath". If all 
     * dependencies are already present in the LibraryPath file location, then there
     * is no need to add any values to this vector. All libraries, whether a dependency
     * or the actual JNI library needed, should be included in this list, should they
     * need to be downloaded.
     */
    public static Vector<String> DependencyPaths = new Vector();
    
    /**
     * The NativeLibraries vector list should contain all of the JNI libraries that
     * implement the native functionality of the classes defined in this namespace.
     */
    public static Vector<String> NativeLibraries = new Vector();
    /**
     * The InitializePrimitives function is used to load all JNI libraries needed
     * to provide the native functionality for the classes within this library.
     * @return Returns true if the function successfully loaded all libraries,
     * false if there was a problem doing so.
     */
    public static boolean InitializePrimitives(){
        boolean retval = true;
        try{
            String separator = System.getProperty("file.separator");
            String binpath = System.getProperty("java.home");
            String archtype = System.getProperty("os.arch");
            String osname = System.getProperty("os.name");
            String osversion = System.getProperty("os.version");
            LibraryPath = System.getProperty("user.home");
            System.out.println("***********************************************");
            System.out.println("** ObjectiveMedia Java Implementation");
            System.out.println("** Version " + Version);
            System.out.println("***********************************************");
            System.out.println("\tPath Separator = " + separator);
            System.out.println("\tJava Binary Location = " + binpath);
            System.out.println("\tSystem Architecture = " + archtype);
            System.out.println("\tOperating System = " + osname);
            System.out.println("\tOS version = " + osversion);
            
            System.out.println("Initializing com.mti.primitives JNI libraries...");
            System.out.println("\tCopying dependencies to Library Path...");
            //TODO: Add function to copy files to Library Path.
            System.out.println("\tLoading JNI Libraries");
            if(!LibraryPath.endsWith(separator))
                LibraryPath = LibraryPath + separator;
            LibraryPath += "objectivemedia" + separator;
            java.io.File libfolder = new java.io.File(LibraryPath);
            if(!libfolder.exists()){
                libfolder.mkdir();
            }
            String resourcePath = "os/win/x64/";
            if(osname.toLowerCase().contains("win")){
                if(archtype.contains("amd")){
                    resourcePath = "os/win/x64/";
                    DependencyPaths.add("libwinpthread-1.dll");
                    DependencyPaths.add("libgcc_s_seh-1.dll");
                    DependencyPaths.add("libstdc++-6.dll");
                    
                    NativeLibraries.add("objectivemedia_win64.dll");
                }
                else{
                    resourcePath = "os/win/x86/";
                    DependencyPaths.add("libwinpthread-1.dll");
                    DependencyPaths.add("libgcc_s_dw2-1.dll");
                    DependencyPaths.add("libstdc++-6.dll");
                    
                    NativeLibraries.add("objectivemedia_win32.dll");
                }
            }
            else if(osname.toLowerCase().contains("lin")){
                if(archtype.contains("amd") || archtype.contains("_64")){
                    resourcePath = "os/lin/x64/";
                    NativeLibraries.add("objectivemedia_lin64.so");
                }
                else{
                    resourcePath = "os/lin/x86/";
                    NativeLibraries.add("objectivemedia_lin32.so");
                }
            }
            else if(osname.toLowerCase().contains("mac")){
                if(archtype.contains("amd") || archtype.contains("_64")){
                    resourcePath = "os/mac/x64/";
                    NativeLibraries.add("objectivemedia_mac64.so");
                }
                else{
                    resourcePath = "os/mac/x86/";
                    NativeLibraries.add("objectivemedia_mac32.so");
                }
            }
            for(int x = 0; x < DependencyPaths.size(); x++){
                String dst = LibraryPath + DependencyPaths.get(x);
                String src = resourcePath + DependencyPaths.get(x);
                System.out.println("\t\t Copying " + src + " to " + dst);
                CopyURL(src, dst);
                System.out.println("\t\t Loading " + dst);
                System.load(dst);
            }
            for(int x = 0; x < NativeLibraries.size(); x++){
                String dst = LibraryPath + NativeLibraries.get(x);
                String src = resourcePath + NativeLibraries.get(x);
                //System.out.println("\t\t Copying " + src + " to " + dst);
                CopyURL(src, dst);
                System.out.println("\t\t Loading " + dst);
                System.load(dst);
            }
        }catch(Exception e){
            System.out.println(e.getMessage());
            System.out.println(e.getStackTrace().toString());
            retval = false;
        }
        return retval;
    }
    
    public static boolean CopyURL(String murl, String dest)
    {
        boolean retval = false;
        System.out.println("Copying " + murl + " to " + dest);
          try
          {
              BufferedInputStream is = new BufferedInputStream(Primitives.class.getResourceAsStream(murl));
              
              // Print info about resource
              FileOutputStream fos=null;

              fos = new FileOutputStream(dest);
              byte[] b = new byte[is.available()];
              is.read(b);
              fos.write(b);

              is.close();
              fos.close();
              retval = true;
          }
          catch (MalformedURLException e)
          { 
              System.err.println(e.toString()); 
          }
          catch (IOException e)
          { 
              System.err.println(e.toString());
          }
        return retval;

    }
}
